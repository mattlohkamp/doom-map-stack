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
//  - Focus: the first time a dms map opens, brings the editor to the front (Windows would
//    otherwise leave it behind the window the mapper launched it from). Not on reloads.
//
// Two editor functions it needs aren't public plugin API (General.OpenMapFileWithOptions and
// Renderer2D.PositionView/ScaleView); they're called by reflection. If an editor upgrade
// renames them, reload fails with a message in the editor's error list, nothing worse.

using System;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
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
        private DateTime warnedWrite;    // the on-disk version last warned about
        private int warnTicks;           // seconds since the warning was last shown
        private bool savedSinceLoad;     // the mapper saved since the map was (re)loaded
        private bool reloading;
        private string lastState;
        private bool broughtToFront;     // once per editor run
        private bool pendingFront;

        [DllImport("user32.dll")] private static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hWnd, IntPtr processId);
        [DllImport("kernel32.dll")] private static extern uint GetCurrentThreadId();
        [DllImport("user32.dll")] private static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
        [DllImport("user32.dll")] private static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")] private static extern bool BringWindowToTop(IntPtr hWnd);

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

        public override void OnMapOpenEnd()
        {
            savedSinceLoad = false;
            Track();
            // The first dms map this editor opens: come to the front. Windows keeps a program that
            // starts slowly behind the window the mapper is in (the launcher has finished by then).
            // Never on live reloads, so a rebuild doesn't pull the editor over what the mapper's doing.
            if (watched != null && !reloading && !broughtToFront)
            {
                broughtToFront = true;
                pendingFront = true;   // done on the next tick, once the window has finished showing
            }
        }

        public override void OnMapSaveEnd(SavePurpose purpose)
        {
            // Our own saves change the file too; remember them so they don't trigger a reload.
            if (purpose != SavePurpose.Testing) { savedSinceLoad = true; Track(); }
        }

        public override void OnMapCloseBegin()
        {
            if (reloading) return;  // our own close-and-reopen: the map stays open as far as dms knows
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
            warnedWrite = DateTime.MinValue;
            WriteState(path, true, Unsaved());
        }

        // The editor keeps IsChanged set after the mapper undoes every edit. With nothing left to
        // undo and no save since the map was loaded, the map is exactly what was loaded: clean.
        private bool Unsaved()
        {
            if (!General.Map.IsChanged) return false;
            if (savedSinceLoad) return true;
            try { return General.Map.UndoRedo.NextUndo != null; }
            catch (Exception) { return true; }
        }

        private void BringToFront()
        {
            Form main = General.Interface as Form;
            if (main == null) return;
            if (main.WindowState == FormWindowState.Minimized) main.WindowState = FormWindowState.Normal;
            IntPtr hwnd = main.Handle;
            IntPtr fg = GetForegroundWindow();
            if (fg == hwnd) return;
            // Windows only lets the program the mapper is using change the foreground window;
            // sharing its input state for a moment counts as that.
            uint fgThread = fg != IntPtr.Zero ? GetWindowThreadProcessId(fg, IntPtr.Zero) : 0;
            uint me = GetCurrentThreadId();
            bool attached = fgThread != 0 && fgThread != me && AttachThreadInput(me, fgThread, true);
            try
            {
                BringWindowToTop(hwnd);
                SetForegroundWindow(hwnd);
                main.Activate();
            }
            finally
            {
                if (attached) AttachThreadInput(me, fgThread, false);
            }
        }

        private void OnTick(object sender, EventArgs e)
        {
            if (pendingFront)
            {
                pendingFront = false;
                try { BringToFront(); }
                catch (Exception ex) { General.ErrorLogger.Add(ErrorType.Warning, "dms bridge: " + ex.Message); }
            }
            if (reloading || watched == null || General.Map == null) return;
            try
            {
                bool unsaved = Unsaved();
                WriteState(watched, true, unsaved);

                FileInfo fi = new FileInfo(watched);
                if (!fi.Exists) return;
                if (fi.LastWriteTimeUtc == knownWrite && fi.Length == knownLength) return;

                if (unsaved)
                {
                    // Warn with a sound once for each new version on disk, then repeat the text
                    // quietly every 10 s (the editor clears status messages after a while).
                    const string msg = "dms: a newer version of this map is on disk. Save your changes and run Pull Map, or undo all of them to get the new version.";
                    if (fi.LastWriteTimeUtc != warnedWrite)
                    {
                        General.Interface.DisplayStatus(StatusType.Warning, msg);
                        warnedWrite = fi.LastWriteTimeUtc;
                        warnTicks = 0;
                    }
                    else if (++warnTicks >= 10)
                    {
                        General.Interface.DisplayStatus(StatusType.Info, msg);
                        warnTicks = 0;
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

                BindingFlags any = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;
                MethodInfo close = typeof(General).GetMethod("CloseMap", any, null, Type.EmptyTypes, null);
                MethodInfo open = typeof(General).GetMethod("OpenMapFileWithOptions", any);
                if (close == null) throw new MissingMethodException("General.CloseMap");
                if (open == null) throw new MissingMethodException("General.OpenMapFileWithOptions");

                // Close the map first, as the editor's own Open does: OpenMapFileWithOptions doesn't
                // dispose the open map, and its leftover handle on the WAD makes the next save fail
                // ("target file is locked by Builder"). Only called with no unsaved changes; the
                // "changed" flag can still be set after undoing every edit, so clear it, or the
                // editor would ask whether to save.
                General.Map.IsChanged = false;
                if (!(bool)close.Invoke(null, null)) return;
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
