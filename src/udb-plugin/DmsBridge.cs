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
//  - Send to Claude (Ctrl+Shift+N, Ctrl+right click menu, Tools menu; Actions.cfg): a note about the selected sectors,
//    lines or things, or what's under the mouse, appended to build\<map>\inbox.jsonl in the
//    same format as dms's own notes (src/dms/inbox.py).
//
// Two editor functions it needs aren't public plugin API (General.OpenMapFileWithOptions and
// Renderer2D.PositionView/ScaleView); they're called by reflection. If an editor upgrade
// renames them, reload fails with a message in the editor's error list, nothing worse.

using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Forms;
using CodeImp.DoomBuilder;
using CodeImp.DoomBuilder.Actions;
using CodeImp.DoomBuilder.Editing;
using CodeImp.DoomBuilder.Geometry;
using CodeImp.DoomBuilder.Map;
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
            General.Actions.BindMethods(this);
            AddToolsMenu();
        }

        public override void Dispose()
        {
            if (timer != null) { timer.Stop(); timer.Dispose(); timer = null; }
            General.Actions.UnbindMethods(this);
            if (toolsItem != null) { General.Interface.RemoveMenu(toolsItem); toolsItem = null; }
            base.Dispose();
        }

        // ---------------------------------------------------------------- Send to Claude

        [BeginAction("sendtoclaude")]
        public void SendToClaude()
        {
            Compose(null);
        }

        // Ctrl+right click: a small menu at the mouse. The spot is remembered now, because by the
        // time the menu item is clicked the mouse is over the menu, not the map.
        [BeginAction("claudemenu")]
        public void ClaudeMenu()
        {
            ClassicMode mode = General.Editing.Mode as ClassicMode;
            Vector2D? at = mode != null && mode.IsMouseInside ? (Vector2D?)mode.MouseMapPos : null;
            ContextMenuStrip menu = new ContextMenuStrip();
            ToolStripMenuItem item = new ToolStripMenuItem("Message Claude about this...");
            item.ShortcutKeyDisplayString = "Ctrl+Shift+N";
            item.Click += delegate { Compose(at); };
            menu.Items.Add(item);
            menu.Closed += delegate { menu.BeginInvoke(new MethodInvoker(menu.Dispose)); };
            menu.Show(Cursor.Position);
        }

        private ToolStripMenuItem toolsItem;  // Tools > Send to Claude...

        private void AddToolsMenu()
        {
            toolsItem = new ToolStripMenuItem("Send to Claude...");
            toolsItem.ShortcutKeyDisplayString = "Ctrl+Shift+N";
            toolsItem.ToolTipText = "A note to Claude about the selected sectors, lines or things (maps opened with Edit Map)";
            toolsItem.Click += delegate { Compose(null); };
            General.Interface.AddMenu(toolsItem, MenuSection.ToolsTesting);
        }

        // The note box, then the note into the map's inbox. `at`: the spot to use when nothing is
        // selected (null = wherever the mouse is now).
        private void Compose(Vector2D? at)
        {
            if (watched == null || General.Map == null)
            {
                General.Interface.DisplayStatus(StatusType.Warning,
                    "dms: Send to Claude only works on maps opened with Edit Map.");
                return;
            }
            try
            {
                List<string> about = new List<string>();   // JSON objects, first = the main one
                string pos = null;
                List<string> props = new List<string>();
                MapSet map = General.Map.Map;
                foreach (Thing t in map.GetSelectedThings(true)) about.Add(Describe(t, props, ref pos));
                foreach (Linedef l in map.GetSelectedLinedefs(true)) about.Add(Describe(l, props, ref pos));
                foreach (Sector s in map.GetSelectedSectors(true)) about.Add(Describe(s, props, ref pos));
                string summary;
                if (about.Count == 0)
                {
                    // Nothing selected: what's under the mouse (a thing, else a line, else the sector).
                    ClassicMode mode = General.Editing.Mode as ClassicMode;
                    if (at == null && (mode == null || !mode.IsMouseInside))
                    {
                        General.Interface.DisplayStatus(StatusType.Warning,
                            "dms: select something, or point at it with the mouse, then Send to Claude.");
                        return;
                    }
                    Vector2D m = at != null ? at.Value : mode.MouseMapPos;
                    pos = "[" + Num(m.x) + ", " + Num(m.y) + "]";
                    Thing t = map.NearestThingSquareRange(m, 24);
                    Linedef l = t == null ? map.NearestLinedefRange(m, 8) : null;
                    Sector s = t == null && l == null ? map.GetSectorByCoordinates(m) : null;
                    string ignored = null;
                    if (t != null) about.Add(Describe(t, props, ref ignored));
                    else if (l != null) about.Add(Describe(l, props, ref ignored));
                    else if (s != null) about.Add(Describe(s, props, ref ignored));
                    summary = "the spot (" + Num(m.x) + ", " + Num(m.y) + ")";
                }
                else
                {
                    summary = about.Count == 1 ? "the selected element" : about.Count + " selected elements";
                }

                string text = NoteForm.Ask(summary);
                if (text == null) return;

                string dir = Path.GetDirectoryName(watched);
                string inbox = Path.Combine(dir, "inbox.jsonl");
                int id = NextNoteId(inbox);
                StringBuilder j = new StringBuilder();
                j.Append("{\"event\": \"note\", \"id\": ").Append(id);
                j.Append(", \"time\": ").Append(Js(DateTime.Now.ToString("yyyy-MM-ddTHH:mm:sszzz", CultureInfo.InvariantCulture)));
                j.Append(", \"map\": ").Append(Js(Path.GetFileName(dir)));
                j.Append(", \"source\": \"editor\", \"text\": ").Append(Js(text.Trim()));
                if (pos != null) j.Append(", \"pos\": ").Append(pos);
                if (about.Count > 0) j.Append(", \"target\": ").Append(about[0]);
                if (about.Count > 1) j.Append(", \"selection\": [").Append(string.Join(", ", about.ToArray())).Append("]");
                if (props.Count > 0) j.Append(", \"props\": ").Append(props[0]);
                j.Append("}\n");
                File.AppendAllText(inbox, j.ToString(), new UTF8Encoding(false));
                if (ClaudeListening(dir))
                    General.Interface.DisplayStatus(StatusType.Info, "dms: note #" + id + " sent to Claude.");
                else
                    General.Interface.DisplayStatus(StatusType.Warning, "dms: note #" + id +
                        " saved, but Claude isn't watching notes (no dms watch): tell Claude to check them.");
            }
            catch (Exception ex)
            {
                General.ErrorLogger.Add(ErrorType.Error, "dms bridge: Send to Claude failed: " + ex.Message);
                General.Interface.DisplayStatus(StatusType.Warning, "dms: the note couldn't be sent (see the error list).");
            }
        }

        // Whether a `dms watch` covering this map wrote build\claude-watch.json in the last 10 s
        // (inbox.listening in src/dms/inbox.py: {"time": ..., "maps": "*" or ["name", ...]}).
        private static bool ClaudeListening(string mapBuildDir)
        {
            try
            {
                string p = Path.Combine(Path.GetDirectoryName(mapBuildDir), "claude-watch.json");
                if (!File.Exists(p) || (DateTime.UtcNow - File.GetLastWriteTimeUtc(p)).TotalSeconds > 10) return false;
                string s = File.ReadAllText(p);
                return s.Contains("\"maps\": \"*\"") || s.Contains("\"" + Path.GetFileName(mapBuildDir) + "\"");
            }
            catch (Exception) { return false; }
        }

        private static int NextNoteId(string inbox)
        {
            int max = 0;
            if (File.Exists(inbox))
                foreach (Match m in Regex.Matches(File.ReadAllText(inbox), "\"id\":\\s*(\\d+)"))
                    max = Math.Max(max, int.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture));
            return max + 1;
        }

        private static string Gid(UniFields f)
        {
            return f != null && f.ContainsKey("user_gid") && f["user_gid"].Value != null ? f["user_gid"].Value.ToString() : null;
        }

        private static string Element(string kind, int index, string gid, string extra)
        {
            return "{\"kind\": \"" + kind + "\", \"index\": " + index + (gid != null ? ", \"gid\": " + Js(gid) : "") + extra + "}";
        }

        // Each Describe returns the element as JSON, sets pos to its centre if not set yet, and
        // records the main element's key properties (so Claude sees what the mapper saw).
        private static string Describe(Thing t, List<string> props, ref string pos)
        {
            if (pos == null) pos = "[" + Num(t.Position.x) + ", " + Num(t.Position.y) + "]";
            if (props.Count == 0)
                props.Add("{\"type\": " + t.Type + ", \"angle\": " + t.AngleDoom + ", \"z\": " + Num(t.Position.z) + "}");
            return Element("thing", t.Index, Gid(t.Fields), ", \"type\": " + t.Type);
        }

        private static string Describe(Linedef l, List<string> props, ref string pos)
        {
            Vector2D a = l.Start.Position, b = l.End.Position;
            if (pos == null) pos = "[" + Num((a.x + b.x) / 2) + ", " + Num((a.y + b.y) / 2) + "]";
            if (props.Count == 0)
            {
                string tex = l.Front != null ? l.Front.MiddleTexture + "/" + l.Front.HighTexture + "/" + l.Front.LowTexture : "-";
                props.Add("{\"ends\": [[" + Num(a.x) + ", " + Num(a.y) + "], [" + Num(b.x) + ", " + Num(b.y) + "]]"
                          + ", \"two_sided\": " + (l.Back != null ? "true" : "false") + ", \"special\": " + l.Action
                          + ", \"front_textures_mid_upper_lower\": " + Js(tex) + "}");
            }
            return Element("linedef", l.Index, Gid(l.Fields), "");
        }

        private static string Describe(Sector s, List<string> props, ref string pos)
        {
            RectangleF box = s.BBox;
            if (pos == null) pos = "[" + Num(box.X + box.Width / 2) + ", " + Num(box.Y + box.Height / 2) + "]";
            if (props.Count == 0)
                props.Add("{\"floor\": " + s.FloorHeight + ", \"ceiling\": " + s.CeilHeight + ", \"light\": " + s.Brightness
                          + ", \"floor_flat\": " + Js(s.FloorTexture) + ", \"ceiling_flat\": " + Js(s.CeilTexture) + "}");
            return Element("sector", s.Index, Gid(s.Fields), "");
        }

        private static string Num(double v)
        {
            return Math.Round(v, 1).ToString("0.#", CultureInfo.InvariantCulture);
        }

        private static string Js(string s)
        {
            if (s == null) return "null";
            StringBuilder b = new StringBuilder("\"");
            foreach (char c in s)
            {
                if (c == '"' || c == '\\') b.Append('\\').Append(c);
                else if (c == '\n') b.Append("\\n");
                else if (c == '\r') b.Append("\\r");
                else if (c == '\t') b.Append("\\t");
                else if (c < ' ') b.Append("\\u").Append(((int)c).ToString("x4"));
                else b.Append(c);
            }
            return b.Append('"').ToString();
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
                // A reminder, after the editor's own "ready" status (the mapper asked for one).
                General.Interface.DisplayStatus(StatusType.Info,
                    "dms: to send Claude a note, select something (or point at it) and press Ctrl+Shift+N, or Ctrl+right click.");
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
            // Swap it in atomically: deleting first left a moment with no file, and a reader
            // (dms build, the board) then thought the editor was closed.
            if (File.Exists(statePath)) File.Replace(tmp, statePath, null);
            else File.Move(tmp, statePath);
        }
    }

    // The note box for Send to Claude: Enter sends, Shift+Enter is a new line, Esc cancels.
    internal class NoteForm : Form
    {
        private readonly TextBox box = new TextBox();

        private NoteForm(string about)
        {
            Text = "Send to Claude";
            FormBorderStyle = FormBorderStyle.FixedDialog;
            StartPosition = FormStartPosition.CenterParent;
            MinimizeBox = false;
            MaximizeBox = false;
            ShowInTaskbar = false;
            ClientSize = new Size(420, 168);
            KeyPreview = true;

            Label label = new Label();
            label.Text = "Note for Claude about " + about + ":";
            label.SetBounds(10, 10, 400, 18);

            box.Multiline = true;
            box.AcceptsReturn = true;
            box.ScrollBars = ScrollBars.Vertical;
            box.SetBounds(10, 32, 400, 92);

            Label hint = new Label();
            hint.Text = "Enter sends - Shift+Enter: new line - Esc cancels";
            hint.ForeColor = SystemColors.GrayText;
            hint.SetBounds(10, 136, 230, 18);

            Button send = new Button();
            send.Text = "Send";
            send.SetBounds(250, 132, 75, 26);
            send.Click += delegate { Finish(); };
            Button cancel = new Button();
            cancel.Text = "Cancel";
            cancel.DialogResult = DialogResult.Cancel;
            cancel.SetBounds(335, 132, 75, 26);

            CancelButton = cancel;
            Controls.AddRange(new Control[] { label, box, hint, send, cancel });
            box.KeyDown += delegate(object s, KeyEventArgs e)
            {
                if (e.KeyCode == Keys.Enter && !e.Shift) { e.SuppressKeyPress = true; Finish(); }
            };
        }

        private void Finish()
        {
            if (box.Text.Trim().Length == 0) return;
            DialogResult = DialogResult.OK;
            Close();
        }

        // The note's text, or null if cancelled.
        public static string Ask(string about)
        {
            using (NoteForm f = new NoteForm(about))
            {
                IWin32Window owner = General.Interface as IWin32Window;
                return f.ShowDialog(owner) == DialogResult.OK ? f.box.Text : null;
            }
        }
    }
}
