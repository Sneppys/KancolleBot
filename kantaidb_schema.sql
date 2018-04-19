BEGIN TRANSACTION;
CREATE TABLE "ShipBase" (
	`ShipID`	INTEGER NOT NULL UNIQUE,
	`Name`	TEXT NOT NULL,
	`Rarity`	INTEGER NOT NULL,
	`ShipType`	INTEGER NOT NULL,
	`Image_Default`	BLOB NOT NULL,
	`Image_Damaged`	BLOB NOT NULL,
	`Image_Small`	BLOB NOT NULL,
	`Image_Small_Damaged`	BLOB NOT NULL,
	`Remodels_Into`	INTEGER DEFAULT 0,
	`Remodels_From`	INTEGER DEFAULT 0,
	`Remodel_Level`	INTEGER DEFAULT 0,
	`Can_Drop`	INTEGER DEFAULT 1,
	`Can_Craft`	INTEGER DEFAULT 1,
	PRIMARY KEY(`ShipID`)
);
COMMIT;
