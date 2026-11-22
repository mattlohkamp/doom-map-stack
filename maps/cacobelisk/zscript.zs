version "4.10"

// Cacobelisk's own script (dms packs it into this map's WAD; it runs on this map only).
// In-game note #1 and the follow-up in chat (2026-11-22): the start is a broken elevator. The switch ahead of the platform lowers it
// (Floor_LowerByValue on CAR_TAG, set in map.py) down the shaft; when it lands, its light starts
// to flicker and the platform throws sparks (with their sound) off the shaft walls, for good.

class CacobeliskElevator : EventHandler
{
	const CAR_TAG = 1;          // the car's sector tag (map.py CAR_TAG)
	const LANDED_Z = -256;      // its floor once down (map.py -DROP)

	const CLOSET_TAG = 2;       // the start closet (map.py CLOSET_TAG)

	// The closet breathes: its light fades between dim and dimmer, 3 s each way (Light_Glow: tag,
	// upper, lower, tics), from the moment the level loads (again after H).
	override void WorldLoaded(WorldEvent e)
	{
		if (e.IsSaveGame) return;   // a saved game has it running already
		Level.ExecuteSpecial(Light_Glow, null, null, false, CLOSET_TAG, 92, 60, 105);
	}

	bool riding;
	bool broken;
	int nextSpark;

	override void WorldLineActivated(WorldEvent e)
	{
		Line ln = e.ActivatedLine;
		// The top switch (Floor_LowerByValue) or the bottom call switch (Floor_MoveToValue, note #10).
		if (ln != null && (ln.special == Floor_LowerByValue || ln.special == Floor_MoveToValue)
			&& ln.args[0] == CAR_TAG && !riding)
		{
			riding = true;
			Console.Printf("[DMS] CacobeliskElevator: the platform is going down");
			LockSwitches(ln);
		}
	}

	// Note #12: once either switch is used, both are done for good: the other one loses its special
	// (from the bottom of the shaft the top switch could still be reached, and lowered the platform
	// another 256) and shows its "on" texture, like the one that was pressed.
	void LockSwitches(Line used)
	{
		TextureID off = TexMan.CheckForTexture("SW1GRAY", TexMan.Type_Wall);
		TextureID on = TexMan.CheckForTexture("SW2GRAY", TexMan.Type_Wall);
		for (int i = 0; i < Level.Lines.Size(); i++)
		{
			Line l = Level.Lines[i];
			if (l == used || l.args[0] != CAR_TAG
				|| (l.special != Floor_LowerByValue && l.special != Floor_MoveToValue))
				continue;
			l.special = 0;
			for (int s = 0; s < 2; s++)
			{
				Side sd = l.sidedef[s];
				if (sd == null)
					continue;
				for (int part = Side.top; part <= Side.bottom; part++)
				{
					if (sd.GetTexture(part) == off)
						sd.SetTexture(part, on);
				}
			}
		}
	}

	override void WorldTick()
	{
		if (!riding)
			return;
		Sector car = FindCar();
		if (car == null)
			return;
		if (!broken)
		{
			if (car.floorplane.ZAtPoint(car.centerspot) > LANDED_Z + 0.5)
				return;
			broken = true;
			// Light_Flicker (tag, upper, lower): the car's light jumps between bright and dim.
			Level.ExecuteSpecial(Light_Flicker, null, null, false, CAR_TAG, 144, 40);
			for (int i = 0; i < 3; i++)   // the bang on landing
				Spark(car);
			nextSpark = Level.maptime + Random(20, 60);
			Console.Printf("[DMS] CacobeliskElevator: landed; the car is broken (flicker, sparks)");
			return;
		}
		if (Level.maptime >= nextSpark)
		{
			Spark(car);
			if (Random(0, 3) == 0)
				Spark(car);     // now and then two at once
			nextSpark = Level.maptime + Random(25, 140);
		}
	}

	// The platform: of the sectors tagged CAR_TAG (the platform and the switch niche's floor, which
	// go down together), the one with the lowest floor (the niche's sill is 16 higher).
	Sector FindCar()
	{
		let it = Level.CreateSectorTagIterator(CAR_TAG);
		Sector best = null;
		int i;
		while ((i = it.Next()) >= 0)
		{
			Sector s = Level.Sectors[i];
			if (best == null || s.floorplane.ZAtPoint(s.centerspot) < best.floorplane.ZAtPoint(best.centerspot))
				best = s;
		}
		return best;
	}

	// A spark (UZDoom's Spark: a burst of particles and the "world/spark" sound) off a random spot on
	// one of the shaft walls, just above the landed platform, spraying across it.
	void Spark(Sector car)
	{
		Array<Line> walls;
		for (int i = 0; i < car.lines.Size(); i++)
		{
			// The shaft's walls: blocking lines onto the solid blocks around it (map.py shaft_side).
			if (car.lines[i].sidedef[1] == null || (car.lines[i].flags & Line.ML_BLOCKING))
				walls.Push(car.lines[i]);
		}
		if (walls.Size() == 0)
			return;
		Line w = walls[Random(0, walls.Size() - 1)];
		Vector2 d = w.delta;
		Vector2 inward = (d.y, -d.x).Unit();   // the front (car) side is on the line's right
		Vector2 at = w.v1.p + d * FRandom(0.1, 0.9) + inward * 4;
		double z = car.floorplane.ZAtPoint(at) + FRandom(12, 56);
		// A few spark actors, reused in turn (destroying one could cut its sound short).
		Actor s;
		if (sparks.Size() < 4)
		{
			s = Actor.Spawn("Spark", (at.x, at.y, z));
			if (s == null)
				return;
			sparks.Push(s);
		}
		else
		{
			s = sparks[sparkTurn++ % sparks.Size()];
			s.SetOrigin((at.x, at.y, z), false);
		}
		s.angle = atan2(inward.y, inward.x);
		s.args[0] = Random(16, 40);
		s.Activate(null);
	}

	Array<Actor> sparks;
	int sparkTurn;
}

// Note #8: the obelisks' reveal. Each starts as a plain pillar up to the ceiling (its sleeve, map.py
// monolith). When the player crosses the line between a pair (the middle of the two slabs, going north
// up the hall), both sleeves sink slowly into their bases (Floor_LowerToLowest: down to the base, the
// lowest floor beside them), down out of their slots in the ceiling, uncovering the carved slabs, a
// cacodemon on the one that has one (note #11: only the switch obelisk; spawned now, still hidden inside
// the sleeve),
// and their glow lights come on. Pairs go one at a time as they're passed. Everything is found from
// the map: pair i's sleeves are tagged SLEEVE_TAG + i, the slab with a cacodemon CACO_TAG + i, its
// glow lights have thing id GLOW_TID + i (map.py).
class CacobeliskObelisks : EventHandler
{
	const SLEEVE_TAG = 100;
	const CACO_TAG = 200;
	const GLOW_TID = 100;
	// Sinking speeds, units a tic. The switch obelisk 0.5 (note #9: the 232 down in about 13 s); the
	// others half that (the mapper, 2026-11-22), about 26 s, so the switch one is the quick one.
	const SINK_SWITCH = 0.5;
	// Note #23: the sleeves stop at the altars' height (map.py: -DROP + 16), not at their base (8 lower),
	// leaving an 8-high rim of the sleeve round each slab.
	const SLEEVE_REST = -240;
	const SINK_OTHERS = 0.25;

	Array<double> pairY;         // the line between pair i's obelisks (their middle, north-south)
	Array<bool> revealed;
	bool ready;

	// Mapper, 2026-11-22: the switch obelisk's face is splattered with blood of a colour nothing else
	// bleeds (luminous violet: not human red, not cacodemon blue): UZDoom's own blood splats, sprayed
	// in that colour. A splat is sprayed once the sinking sleeve has passed below it (sprayed earlier,
	// it would land on the sleeve), so each appears as the stone behind it is uncovered.
	// Note #17, "more pronounced": brighter and more saturated (was 0xA030FF), seven marks (was three):
	// the two biggest splats and smears that run down the stone, overlapping across the face.
	const SPLAT_COLOR = 0xFFC020FF;
	static const String SPLAT_DECAL[] = { "BloodSplat1", "BloodSplat2", "BloodSplat1", "BloodSmear",
		"BloodSplat2", "BloodSmear", "BloodSplat1" };
	static const double SPLAT_ALONG[] = { -16, 4, 18, -6, 12, 8, -12 };    // along the face from its middle
	static const double SPLAT_UP[] = { 100, 92, 74, 66, 50, 36, 30 };     // above the base
	Array<double> splatX, splatY, splatZ, splatAngle;
	Array<int> splatSleeve, splatKind;

	// Note #13: the sleeves sink silently (map.py: silent); instead each plays a low, quiet rumble
	// (UZDoom's world/quake, pitched down) while it moves, fading out over a second when it stops.
	const RUMBLE_VOLUME = 0.5;     // note #23 (was 0.33; 0.06 was inaudible, then 0.2)
	const RUMBLE_REACH = 0.5;      // attenuation: half the normal falloff, so it carries about twice as far
	const RUMBLE_PITCH = 0.5;                      // an octave down, half speed (was 0.75)
	const RUMBLE_FADE = 35;                         // tics
	Array<Actor> rumbles;
	Array<int> rumbleSleeve, rumbleFade;
	Array<double> rumbleLastZ;

	void FindPairs()
	{
		for (int i = 0; i < 64; i++)
		{
			let it = Level.CreateSectorTagIterator(SLEEVE_TAG + i);
			double sum = 0;
			int n = 0, s;
			while ((s = it.Next()) >= 0)
			{
				sum += Level.Sectors[s].centerspot.y;
				n++;
			}
			if (n == 0)
				break;
			pairY.Push(sum / n);
			revealed.Push(false);
			Hum(i);
		}
		Console.Printf("[DMS] CacobeliskObelisks: %d pair(s) waiting", pairY.Size());
	}

	// Note #11: a low rumble from inside the obelisk with the cacodemon (the one to interact with), from
	// the start: UZDoom's earthquake rumble, looped, very quiet, heard only close by.
	void Hum(int i)
	{
		let it = Level.CreateSectorTagIterator(CACO_TAG + i);
		int s;
		while ((s = it.Next()) >= 0)
		{
			Sector slab = Level.Sectors[s];
			Vector2 c = slab.centerspot;
			Actor spot = Actor.Spawn("MapSpot", (c.x, c.y, slab.floorplane.ZAtPoint(c) - 40));
			if (spot != null)
				spot.A_StartSound("world/quake", CHAN_BODY, CHANF_LOOPING, 0.3, ATTN_STATIC);
		}
	}

	override void WorldTick()
	{
		if (!ready)
		{
			ready = true;
			FindPairs();
		}
		PlayerPawn p = players[consoleplayer].mo;
		if (p == null)
			return;
		for (int i = 0; i < pairY.Size(); i++)
		{
			if (!revealed[i] && p.pos.y >= pairY[i])
				Reveal(i, p);
		}
		SpraySplats();
		UpdateRumbles();
	}

	// Note #21: as a pillar comes to rest, a loud, deep "whumph": the blazing door's slam and the lift's
	// stopping clunk, both pitched well down, from where it landed. Played from a spot of its own that
	// stays, so the sound isn't cut when the rumble's spot goes.
	void Thud(Actor at)
	{
		if (at == null)
			return;
		Actor spot = Actor.Spawn("MapSpot", at.pos);
		if (spot == null)
			return;
		spot.A_StartSound("doors/dr2_clos", CHAN_5, 0, 1.0, ATTN_NORM, 0.55);
		spot.A_StartSound("plats/pt1_stop", CHAN_6, 0, 0.8, ATTN_NORM, 0.5);
	}

	// Each rumble plays while its sleeve moves; once the floor stops, it fades out and goes.
	void UpdateRumbles()
	{
		for (int k = rumbles.Size() - 1; k >= 0; k--)
		{
			Actor r = rumbles[k];
			Sector sleeve = Level.Sectors[rumbleSleeve[k]];
			double z = sleeve.floorplane.ZAtPoint(sleeve.centerspot);
			if (rumbleFade[k] < 0)
			{
				if (z != rumbleLastZ[k])
				{
					rumbleLastZ[k] = z;
					continue;                       // still sinking
				}
				rumbleFade[k] = RUMBLE_FADE;
				Thud(r);
			}
			rumbleFade[k]--;
			if (r != null && rumbleFade[k] > 0)
			{
				r.A_SoundVolume(CHAN_BODY, RUMBLE_VOLUME * rumbleFade[k] / RUMBLE_FADE);
				continue;
			}
			if (r != null)
			{
				r.A_StopSound(CHAN_BODY);
				r.Destroy();
			}
			rumbles.Delete(k);
			rumbleSleeve.Delete(k);
			rumbleFade.Delete(k);
			rumbleLastZ.Delete(k);
		}
	}

	// The splats for pair i's switch obelisk (its slab is tagged CACO_TAG + i): spots 12 out from the
	// face (the side towards the hall's middle, x 32), each to spray once its sleeve is below it.
	void QueueSplats(int i)
	{
		let it = Level.CreateSectorTagIterator(CACO_TAG + i);
		int s;
		while ((s = it.Next()) >= 0)
		{
			Sector slab = Level.Sectors[s];
			Vector2 c = slab.centerspot;
			double dir = c.x < 32 ? 1 : -1;               // from the slab towards the aisle
			double faceX = c.x + dir * 16;
			double baseZ = slab.floorplane.ZAtPoint(c) - 128;
			let sleeves = Level.CreateSectorTagIterator(SLEEVE_TAG + i);
			int sl, sleeve = -1;
			while ((sl = sleeves.Next()) >= 0)            // the sleeve round this slab: the nearest one
			{
				if (sleeve < 0 || (Level.Sectors[sl].centerspot - c).Length() < (Level.Sectors[sleeve].centerspot - c).Length())
					sleeve = sl;
			}
			for (int k = 0; k < SPLAT_UP.Size(); k++)
			{
				splatX.Push(faceX + dir * 12);
				splatY.Push(c.y + SPLAT_ALONG[k]);
				splatZ.Push(baseZ + SPLAT_UP[k]);
				splatAngle.Push(dir > 0 ? 180 : 0);
				splatSleeve.Push(sleeve);
				splatKind.Push(k);
			}
		}
	}

	void SpraySplats()
	{
		for (int k = splatX.Size() - 1; k >= 0; k--)
		{
			Sector sleeve = Level.Sectors[splatSleeve[k]];
			if (sleeve.floorplane.ZAtPoint(sleeve.centerspot) > splatZ[k] - 12)   // the sleeve now rests 8 up
				continue;                                  // still covered
			Actor spot = Actor.Spawn("MapSpot", (splatX[k], splatY[k], splatZ[k]));
			if (spot != null)
			{
				spot.angle = splatAngle[k];
				spot.A_SprayDecal(SPLAT_DECAL[splatKind[k]], 32, (0, 0, 0), (0, 0, 0), false, SPLAT_COLOR);
				spot.Destroy();
			}
			splatX.Delete(k);
			splatY.Delete(k);
			splatZ.Delete(k);
			splatAngle.Delete(k);
			splatSleeve.Delete(k);
			splatKind.Delete(k);
		}
	}

	void Reveal(int i, Actor player)
	{
		revealed[i] = true;
		// Each sleeve down to the lowest floor beside it (its base): the switch obelisk's (round a slab
		// tagged CACO_TAG + i) at SINK_SWITCH, the rest at SINK_OTHERS.
		Array<int> switchSlabs;                    // sector numbers (no Vector2 arrays in ZScript)
		let cs = Level.CreateSectorTagIterator(CACO_TAG + i);
		int cso;
		while ((cso = cs.Next()) >= 0)
			switchSlabs.Push(cso);
		let sinking = Level.CreateSectorTagIterator(SLEEVE_TAG + i);
		int si;
		while ((si = sinking.Next()) >= 0)
		{
			Sector sleeve = Level.Sectors[si];
			bool isSwitch = false;
			for (int k = 0; k < switchSlabs.Size(); k++)
				isSwitch |= (sleeve.centerspot - Level.Sectors[switchSlabs[k]].centerspot).Length() < 40;
			double drop = sleeve.floorplane.ZAtPoint(sleeve.centerspot) - SLEEVE_REST;
			Level.CreateFloor(sleeve, Floor.floorLowerByValue, null, isSwitch ? SINK_SWITCH : SINK_OTHERS, drop);
		}
		let it = Level.CreateSectorTagIterator(CACO_TAG + i);
		int s;
		int cacos = 0;
		while ((s = it.Next()) >= 0)
		{
			Sector slab = Level.Sectors[s];
			Vector2 c = slab.centerspot;
			Actor caco = Actor.Spawn("Cacodemon", (c.x, c.y, slab.floorplane.ZAtPoint(c)), ALLOW_REPLACE);
			if (caco != null)
			{
				caco.angle = caco.AngleTo(player);
				// A dark cacodemon (the mapper, 2026-11-22): a dark, mostly see-through silhouette.
				caco.A_SetRenderStyle(1.0, STYLE_Shadow);
				cacos++;
			}
		}
		QueueSplats(i);
		let sleeves = Level.CreateSectorTagIterator(SLEEVE_TAG + i);
		int sl;
		while ((sl = sleeves.Next()) >= 0)
		{
			Sector sleeve = Level.Sectors[sl];
			Vector2 sc = sleeve.centerspot;
			Actor r = Actor.Spawn("MapSpot", (sc.x, sc.y, player.pos.z + 48));
			if (r == null)
				continue;
			r.A_StartSound("world/quake", CHAN_BODY, CHANF_LOOPING, RUMBLE_VOLUME, RUMBLE_REACH, RUMBLE_PITCH);
			// Note #23: a sharp clack as it starts: the switch click, pitched a little down, over the
			// lift's starting clunk.
			r.A_StartSound("switches/normbutn", CHAN_5, 0, 1.0, ATTN_NORM, 0.75);   // 75% speed (the mapper)
			r.A_StartSound("plats/pt1_strt", CHAN_6, 0, 0.7, ATTN_NORM, 0.75);
			rumbles.Push(r);
			rumbleSleeve.Push(sl);
			rumbleFade.Push(-1);
			rumbleLastZ.Push(1e9);           // "moving": the floor only starts on the next tic
		}
		let lights = Level.CreateActorIterator(GLOW_TID + i);
		Actor l;
		while ((l = lights.Next()) != null)
			l.Activate(null);
		Console.Printf("[DMS] CacobeliskObelisks: pair %d revealed (%d cacodemon(s))", i + 1, cacos);
	}
}
