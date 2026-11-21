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
		if (e.Name != "dms_mark" || e.Player != consoleplayer) return;
		let p = players[e.Player];
		let mo = p.mo;
		if (!mo) return;
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
