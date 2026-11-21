// dms bridge: an Ultimate Doom Builder plugin that connects the editor to dms.
//
// Compiled by `dms setup` with the C# compiler that ships with Windows (.NET Framework 4.8,
// so C# 5: no string interpolation, no ?. operator) into .tools\udb\Plugins\DmsBridge.dll.
// Written for UDB R4336 (pinned in tools.toml). MIT, like the rest of the repo; it is only
// compiled locally against the GPL editor, never distributed as a binary.
//
// What it does, for maps opened through dms (build\<map>\edit.wad, next to edit.state.json):
//  - Live reload: about once a second, checks whether the open WAD changed on disk (Claude
//    rebuilt the map). With no unsaved changes, it reopens the map in place, keeping the view
//    position, zoom and edit mode. With unsaved changes it reloads nothing and says so in the
//    status bar, so the mapper's work is never thrown away.
//  - Status: writes build\<map>\editor-state.json (open, unsaved changes, file), so dms and
//    the board know whether it's safe to update edit.wad.
//
// Two editor functions it needs aren't public plugin API (General.OpenMapFileWithOptions and
// Renderer2D.PositionView/ScaleView); they're called by reflection. If an editor upgrade
// renames them, reload fails with a message in the editor's error list, nothing worse.

using System;
using System.IO;
using System.Reflection;
using System.Text;
using System.Windows.Forms;
using CodeImp.DoomBuilder;
using CodeImp.DoomBuilder.Plugins;
using CodeImp.DoomBuilder.Windows;

namespace Dms.UdbBridge
{
    public class BridgePlug : Plug
    {
        private Timer timer;
        private string watched;          // full path of the open dms-managed WAD, or null
        private DateTime knownWrite;
        private long knownLength;
        private bool warned;
        private bool reloading;
        private string lastState;

        public override string Name { get { return "dms bridge"; } }

        public override void OnInitialize()
        {
            base.OnInitialize();
            timer = new Timer();
            timer.Interval = 1000;
            timer.Tick += OnTick;
            timer.Start();
        }

        public override void Dispose()
        {
            if (timer != null) { timer.Stop(); timer.Dispose(); timer = null; }
            base.Dispose();
        }

        public override void OnMapOpenEnd() { Track(); }

        public override void OnMapSaveEnd(SavePurpose purpose)
        {
            // Our own saves change the file too; remember them so they don't trigger a reload.
            if (purpose != SavePurpose.Testing) Track();
        }

        public override void OnMapCloseBegin()
        {
            if (watched != null) WriteState(watched, false, false);
            watched = null;
        }

        private static bool IsDmsManaged(string path)
        {
            if (string.IsNullOrEmpty(path)) return false;
            string dir = Path.GetDirectoryName(path);
            return Path.GetFileName(path).Equals("edit.wad", StringComparison.OrdinalIgnoreCase)
                && File.Exists(Path.Combine(dir, "edit.state.json"));
        }

        private void Track()
        {
            string path = General.Map != null ? General.Map.FilePathName : null;
            if (!IsDmsManaged(path)) { watched = null; return; }
            watched = path;
            FileInfo fi = new FileInfo(path);
            knownWrite = fi.LastWriteTimeUtc;
            knownLength = fi.Length;
            warned = false;
            WriteState(path, true, General.Map.IsChanged);
        }

        private void OnTick(object sender, EventArgs e)
        {
            if (reloading || watched == null || General.Map == null) return;
            try
            {
                bool unsaved = General.Map.IsChanged;
                WriteState(watched, true, unsaved);

                FileInfo fi = new FileInfo(watched);
                if (!fi.Exists) return;
                if (fi.LastWriteTimeUtc == knownWrite && fi.Length == knownLength) return;

                if (unsaved)
                {
                    if (!warned)
                    {
                        General.Interface.DisplayStatus(StatusType.Warning,
                            "dms: a newer version of this map is on disk. Save your changes and ask Claude to pull them, or undo them to get the new version.");
                        warned = true;
                    }
                    return;
                }
                Reload();
            }
            catch (Exception ex)
            {
                General.ErrorLogger.Add(ErrorType.Warning, "dms bridge: " + ex.Message);
            }
        }

        private void Reload()
        {
            reloading = true;
            string file = watched;
            try
            {
                object options = General.Map.Options;
                float x = General.Map.Renderer2D.OffsetX;
                float y = General.Map.Renderer2D.OffsetY;
                float scale = General.Map.Renderer2D.Scale;
                string mode = General.Editing.Mode != null ? General.Editing.Mode.GetType().Name : null;

                MethodInfo open = typeof(General).GetMethod("OpenMapFileWithOptions",
                    BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
                if (open == null) throw new MissingMethodException("General.OpenMapFileWithOptions");
                open.Invoke(null, new object[] { file, options });

                if (General.Map != null)
                {
                    if (mode != null) General.Editing.ChangeMode(mode);
                    object r = General.Map.Renderer2D;
                    MethodInfo pos = r.GetType().GetMethod("PositionView");
                    MethodInfo zoom = r.GetType().GetMethod("ScaleView");
                    if (zoom != null) zoom.Invoke(r, new object[] { scale });
                    if (pos != null) pos.Invoke(r, new object[] { x, y });
                    General.Interface.RedrawDisplay();
                    General.Interface.DisplayStatus(StatusType.Info,
                        "dms: reloaded " + Path.GetFileName(Path.GetDirectoryName(file)) + " (updated on disk) at " + DateTime.Now.ToString("HH:mm:ss"));
                }
            }
            catch (Exception ex)
            {
                Exception inner = ex.InnerException ?? ex;
                General.ErrorLogger.Add(ErrorType.Error, "dms bridge: reload failed: " + inner.Message);
            }
            finally
            {
                reloading = false;
                Track();
            }
        }

        private void WriteState(string wadPath, bool open, bool unsaved)
        {
            string json = "{\n"
                + "  \"open\": " + (open ? "true" : "false") + ",\n"
                + "  \"unsaved_changes\": " + (unsaved ? "true" : "false") + ",\n"
                + "  \"file\": \"" + wadPath.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\",\n"
                + "  \"pid\": " + System.Diagnostics.Process.GetCurrentProcess().Id + "\n"
                + "}\n";
            if (json == lastState) return;
            lastState = json;
            string statePath = Path.Combine(Path.GetDirectoryName(wadPath), "editor-state.json");
            string tmp = statePath + ".tmp";
            File.WriteAllText(tmp, json, new UTF8Encoding(false));
            if (File.Exists(statePath)) File.Delete(statePath);
            File.Move(tmp, statePath);
        }
    }
}
