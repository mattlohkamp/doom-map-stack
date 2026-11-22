version "4.10"

// dms devtools: notes for Claude from inside the game. Loaded by `dms play` (-file resources/devtools).
// Written from scratch for this repo (MIT); see src/dms/inbox.py for where the notes go.
//
// Key N (KEYCONF: "netevent dms_mark") -> DmsNotes.NetworkProcess (play scope) logs where
// the player is and what the crosshair is on, takes a screenshot, then opens DmsNoteMenu -> the mapper types a note ->
// the menu logs it. dms reads the lines from the console log (build/<map>/log-play.txt):
//
//   [DMS-NOTE-MARK] <n> pos=<x>,<y>,<z> angle=<a> pitch=<p> sector=<i> hit=<none|wall|floor|ceiling|thing> ...
//   [DMS-NOTE-TEXT] <n> <epoch seconds> <the note>
//   [DMS-NOTE-CANCEL] <n>

class DmsNotes : EventHandler
{
	int marks;  // marks made this session; the menu reads it to number its note

	override void NetworkProcess(ConsoleEvent e)
	{
		if (e.Player != consoleplayer) return;
		let p = players[e.Player];
		let mo = p.mo;
		if (!mo) return;
		if (e.Name == "dms_reload")
		{
			let live = DmsLive(StaticEventHandler.Find("DmsLive"));
			if (live && live.hasLive && !live.restart)
			{
				// dms has already written the latest build into play.wad: reload the map from it and put
				// the player back here (DmsLive.PlayerEntered).
				live.pending = true;
				live.spawn = mo.pos;
				live.spawnAngle = mo.angle;
				live.spawnPitch = mo.pitch;
				Console.Printf("[DMS-RELOAD-INPLACE] %.1f %.1f %.1f build=%d", mo.pos.x, mo.pos.y, mo.pos.z, live.build);
				level.ChangeLevel(level.MapName, 0, CHANGELEVEL_NOINTERMISSION);
			}
			else
			{
				// The map outgrew play.wad (or it isn't a live one): the board (Open Board.cmd) sees this
				// line, rebuilds, and restarts the game here.
				Console.Printf("[DMS-RELOAD] %.1f %.1f %.1f %.1f %.1f", mo.pos.x, mo.pos.y, mo.pos.z, mo.angle, mo.pitch);
				Console.MidPrint(NewSmallFont, "Restarting the game here...\n(this needs the board running: Open Board.cmd)");
			}
			return;
		}
		if (e.Name != "dms_mark") return;
		marks++;

		FLineTraceData t;
		// TRF_ALLACTORS: stop at items too (a shotgun isn't solid), not only at monsters.
		mo.LineTrace(mo.angle, 8192, mo.pitch, TRF_ALLACTORS, p.viewheight, 0, 0, t);
		String hit = "none";
		if (t.HitType == TRACE_HitWall && t.HitLine)
			hit = String.Format("wall line=%d side=%d", t.HitLine.Index(), t.LineSide);
		else if (t.HitType == TRACE_HitFloor && t.HitSector)
			hit = String.Format("floor sector=%d", t.HitSector.Index());
		else if (t.HitType == TRACE_HitCeiling && t.HitSector)
			hit = String.Format("ceiling sector=%d", t.HitSector.Index());
		else if (t.HitType == TRACE_HitActor && t.HitActor)
			// SpawnPoint: where the map placed it (= its TEXTMAP position), even after a monster moved
			// or died. health <= 0: a corpse.
			hit = String.Format("thing class=%s at=%.1f,%.1f spawn=%.1f,%.1f health=%d", t.HitActor.GetClassName(),
				t.HitActor.pos.x, t.HitActor.pos.y, t.HitActor.SpawnPoint.x, t.HitActor.SpawnPoint.y, t.HitActor.health);

		Console.Printf("[DMS-NOTE-MARK] %d pos=%.1f,%.1f,%.1f angle=%.1f pitch=%.1f sector=%d hit=%s at=%.1f,%.1f,%.1f",
			marks, mo.pos.x, mo.pos.y, mo.pos.z, mo.angle, mo.pitch, mo.CurSector.Index(), hit,
			t.HitLocation.x, t.HitLocation.y, t.HitLocation.z);
		// The screenshot: allowed when the player's own setting enablescriptscreenshot is on
		// (`dms play` turns it on; a mod can't run the `screenshot` command). The note box opens
		// two tics later, so the shot shows the game, not the box.
		LevelLocals.MakeScreenShot();
		menuIn = 2;
	}

	int menuIn;  // tics until the note box opens

	override void WorldTick()
	{
		if (menuIn > 0 && --menuIn == 0)
			Menu.SetMenu("DmsNoteMenu");
	}
}

// The note box: a dimmed screen with a prompt, and the engine's text entry on top. Esc cancels.
class DmsNoteMenu : GenericMenu
{
	TextEnterMenu input;
	bool opened;
	int mark;

	override void Init(Menu parent)
	{
		Super.Init(parent);
		let h = DmsNotes(EventHandler.Find("DmsNotes"));
		mark = h ? h.marks : 0;
		DontDim = true;
	}

	override void Ticker()
	{
		Super.Ticker();
		if (!opened)  // after Init: the engine activates this menu once Init returns
		{
			opened = true;
			// The limit is a width in pixels in that font (200 allowed only ~23 characters); allow ~1000.
			input = TextEnterMenu.OpenTextEnter(self, NewSmallFont, "", NewSmallFont.StringWidth("0") * 1000, false);
			input.ActivateMenu();
		}
	}

	override bool MenuEvent(int mkey, bool fromcontroller)
	{
		if (mkey == MKEY_Input && input)
		{
			String text = input.GetText();
			text.Replace("\n", " ");
			if (text.Length() > 0)
				Console.Printf("[DMS-NOTE-TEXT] %d %d %s", mark, SystemTime.Now(), text);
			else
				Console.Printf("[DMS-NOTE-CANCEL] %d", mark);
			Close();
			return true;
		}
		if (mkey == MKEY_Abort)
		{
			Console.Printf("[DMS-NOTE-CANCEL] %d", mark);
			Close();
			return true;
		}
		return Super.MenuEvent(mkey, fromcontroller);
	}

	// The engine's text entry only collects keys; drawing what's been typed is the parent menu's job.
	// So: a prompt, then the text so far (wrapped, with a blinking cursor), then the keys.
	override void Drawer()
	{
		int sw = Screen.GetWidth(), sh = Screen.GetHeight();
		Screen.Dim(0, 0.6, 0, 0, sw, sh);
		Font f = NewSmallFont;
		int scale = max(1, sh / 360);
		int lh = f.GetHeight() * scale;
		int boxw = min(sw - 40, 640 * scale);
		int x = (sw - boxw) / 2, y = sh / 4;

		Screen.DrawText(f, Font.CR_GOLD, x, y, String.Format("Note for Claude (#%d)", mark),
			DTA_ScaleX, scale, DTA_ScaleY, scale);
		y += lh * 2;

		String typed = input ? input.GetText() : "";
		typed = typed .. (((Menu.MenuTime() / 12) % 2 == 0) ? "_" : " ");
		let lines = f.BreakLines(typed, boxw / scale);
		int n = max(1, lines.Count());
		Screen.Dim(Color(255, 24, 24, 32), 0.9, x - 10, y - 8, boxw + 20, n * lh + 16);
		for (int i = 0; i < lines.Count(); i++)
			Screen.DrawText(f, Font.CR_WHITE, x, y + i * lh, lines.StringAt(i), DTA_ScaleX, scale, DTA_ScaleY, scale);
		y += n * lh + 24;

		Screen.DrawText(f, Font.CR_DARKGRAY, x, y, "Enter sends  -  Backspace corrects  -  Esc cancels",
			DTA_ScaleX, scale, DTA_ScaleY, scale);
		Super.Drawer();
	}
}

// The live link with dms (src/dms/live.py). `dms play` runs a play.wad whose lumps dms rewrites in place
// while the game runs; UZDoom reads a lump from disk each time, so:
//  - DMSLIVE (polled every second): Claude's replies, shown here as they come; the build in play.wad;
//    whether the map outgrew play.wad ("restart": then key H asks the board to restart the game).
//  - TEXTMAP: the latest build, which key H loads by reloading the map; the player is put back where
//    they were (PlayerEntered).
// Also, after a restart by the board: dms_spawn / dms_message (CVARINFO) from the command line.
// A static handler, so it survives map reloads; its messages time out on level.totaltime.
class DmsLive : StaticEventHandler
{
	bool hasLive;       // play.wad has a DMSLIVE lump (it's a live play.wad)
	int build;          // the build dms last wrote into play.wad
	bool restart;       // the map outgrew play.wad: H restarts the game instead
	int lastSeq;        // the last message shown
	String status;      // what Claude is doing ("" = nothing): a line near the bottom, with moving dots

	bool pending;       // H was pressed: put the player back at spawn on arrival
	vector3 spawn;
	double spawnAngle, spawnPitch;
	bool started;       // the command-line spawn/message were applied (once per game start)

	Array<String> shown;    // messages on screen, and when each appeared (level.totaltime)
	Array<int> shownAt;

	const SHOW_TICS = 12 * TICRATE;

	void Say(String text)
	{
		shown.Push(text);
		shownAt.Push(level.totaltime);
		Console.Printf("%s", text);
	}

	override void WorldTick()
	{
		if (level.totaltime % TICRATE == 0) Poll();
	}

	void Poll()
	{
		int lump = Wads.FindLump("DMSLIVE");
		if (lump < 0) return;
		hasLive = true;
		Array<String> lines;
		Wads.ReadLump(lump).Split(lines, "\n");
		for (int i = 0; i < lines.Size(); i++)
		{
			String l = lines[i];
			if (l.Left(7) == "status ") { status = l.Mid(7); status.StripRight(); }
			else if (l.Left(6) == "build ") build = l.Mid(6).ToInt();
			else if (l.Left(8) == "restart ") restart = l.Mid(8).ToInt() != 0;
			else if (l.Left(4) == "msg ")
			{
				String rest = l.Mid(4);
				int sp = rest.IndexOf(" ");
				if (sp < 0) continue;
				int seq = rest.Left(sp).ToInt();
				if (seq > lastSeq)
				{
					lastSeq = seq;
					Say(rest.Mid(sp + 1));
				}
			}
		}
	}

	override void PlayerEntered(PlayerEvent e)
	{
		if (e.PlayerNumber != consoleplayer) return;
		let mo = players[e.PlayerNumber].mo;
		if (!mo) return;
		if (pending)
		{
			pending = false;
			Place(mo, spawn, spawnAngle, spawnPitch);
			Say(String.Format("Reloaded in place (build #%d)", build));
			return;
		}
		if (started) return;
		started = true;
		Poll();  // don't repeat messages that were already there when the game started
		let sp = CVar.GetCVar("dms_spawn", players[e.PlayerNumber]);
		if (sp && sp.GetString().Length() > 0)
		{
			Array<String> v;
			sp.GetString().Split(v, " ", TOK_SKIPEMPTY);
			if (v.Size() == 5)
				Place(mo, (v[0].ToDouble(), v[1].ToDouble(), v[2].ToDouble()), v[3].ToDouble(), v[4].ToDouble());
		}
		let msg = CVar.GetCVar("dms_message", players[e.PlayerNumber]);
		if (msg && msg.GetString().Length() > 0)
		{
			Array<String> lines;
			msg.GetString().Split(lines, "|");
			for (int i = 0; i < lines.Size(); i++) Say(lines[i]);
		}
	}

	ui void DrawStatus()
	{
		if (status.Length() == 0) return;
		Font f = NewSmallFont;
		int sw = Screen.GetWidth(), sh = Screen.GetHeight();
		int scale = max(1, sh / 400);
		// Dots that keep moving, so it's clear Claude (and the link) is alive: ".", "..", "...", "".
		String dots = "";
		for (int i = 0; i < (level.totaltime / 12) % 4; i++) dots = dots .. ".";
		String line = "Claude: " .. status .. " " .. dots;
		int w = f.StringWidth("Claude: " .. status .. " ...") * scale;  // without the dots: no jitter
		int x = (sw - w) / 2, y = sh * 3 / 4;
		Screen.Dim(Color(255, 16, 16, 24), 0.7, x - 10, y - 6, w + 20, f.GetHeight() * scale + 12);
		Screen.DrawText(f, Font.CR_SAPPHIRE, x, y, line, DTA_ScaleX, scale, DTA_ScaleY, scale);
	}

	void Place(Actor mo, vector3 pos, double angle, double pitch)
	{
		mo.SetOrigin(pos, false);
		mo.angle = angle;
		mo.pitch = pitch;
		mo.vel = (0, 0, 0);
	}

	// Recent messages in a box at the top of the screen; Claude's status on a line near the bottom.
	override void RenderOverlay(RenderEvent e)
	{
		DrawStatus();
		Array<String> lines;
		for (int i = 0; i < shown.Size(); i++)
			if (level.totaltime - shownAt[i] <= SHOW_TICS) lines.Push(shown[i]);
		if (lines.Size() == 0) return;
		Font f = NewSmallFont;
		int sw = Screen.GetWidth(), sh = Screen.GetHeight();
		int scale = max(1, sh / 400);
		int lh = f.GetHeight() * scale;
		int boxw = min(sw - 40, 760 * scale);
		int x = (sw - boxw) / 2, y = 20 * scale;
		Array<String> wrapped;
		Array<int> first;  // 1 where a message starts (drawn in gold)
		for (int i = 0; i < lines.Size(); i++)
		{
			let b = f.BreakLines(lines[i], boxw / scale);
			for (int j = 0; j < b.Count(); j++) { wrapped.Push(b.StringAt(j)); first.Push(j == 0 ? 1 : 0); }
		}
		Screen.Dim(Color(255, 16, 16, 24), 0.85, x - 12, y - 10, boxw + 24, wrapped.Size() * lh + 20);
		for (int i = 0; i < wrapped.Size(); i++)
			Screen.DrawText(f, first[i] ? Font.CR_GOLD : Font.CR_WHITE, x, y + i * lh, wrapped[i],
				DTA_ScaleX, scale, DTA_ScaleY, scale);
	}
}
