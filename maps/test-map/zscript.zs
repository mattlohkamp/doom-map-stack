version "4.10"

// The test map's own script (dms packs it into this map's WAD; it runs on this map only).

// Quad damage (mapper's request, build #9): Doom has none, so this is UZDoom's PowerDamage (which
// multiplies the player's damage by 4) for 30 seconds, with a blue tint while it lasts. It looks like
// a megasphere, tinted icy blue so it can't be mistaken for one.
class TestMapQuadDamage : PowerupGiver
{
	Default
	{
		Powerup.Type "PowerDamage";
		Powerup.Duration -30;
		Powerup.Color "Blue", 0.2;
		Inventory.PickupMessage "Quad damage!";
		Inventory.PickupSound "misc/p_pkup";
		Inventory.MaxAmount 0;
		Translation "Ice";
		+Inventory.AutoActivate;
		+Inventory.AlwaysPickup;
		+CountItem;
		+FloatBob;
	}
	States
	{
	Spawn:
		MEGA ABCD 6 Bright;
		Loop;
	}
}

class TestMapEvents : EventHandler
{
	const PILLAR_TAG = 2;   // the pillars' sector tag (map.py PILLAR_TAG)
	const CACO_TID = 10;    // the pillar cacos' thing id (map.py CACO_TID)
	const QUAD_TID = 11;    // the map spot for the quad damage (map.py QUAD_TID)

	// Put the quad damage on its map spot in the secret room (not when loading a save: it's in there).
	override void WorldLoaded(WorldEvent e)
	{
		if (e.IsSaveGame)
			return;
		int placed = 0;
		let it = Level.CreateActorIterator(QUAD_TID);
		Actor spot;
		while ((spot = it.Next()) != null)
		{
			if (spot is "TestMapQuadDamage")
				continue;
			Actor.Spawn("TestMapQuadDamage", spot.Pos);
			placed++;
		}
		Console.Printf("[DMS] TestMapEvents: placed %d quad damage", placed);
	}

	// The super shotgun trap: when a pentagram line opens the pillars, wake their cacos, already after
	// the player (shut in the pillars, they'd hear nothing).
	override void WorldLineActivated(WorldEvent e)
	{
		Line ln = e.ActivatedLine;
		if (ln == null || ln.special != Door_Open || ln.args[0] != PILLAR_TAG || e.Thing == null)
			return;
		int woken = 0;
		let it = Level.CreateActorIterator(CACO_TID);
		Actor caco;
		while ((caco = it.Next()) != null)
		{
			if (caco.health <= 0 || caco.target == e.Thing)
				continue;
			caco.target = e.Thing;
			caco.SetState(caco.SeeState);
			woken++;
		}
		Console.Printf("[DMS] TestMapEvents: the pillars open; woke %d caco(s)", woken);
	}
}
