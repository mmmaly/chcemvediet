CREATE TABLE "User"
(
  "Email" text NOT NULL,
  "Password" text NOT NULL,
  "FirstName" text,
  "LastName" text,
  "Street" text,
  "City" text,
  "ZIP" text,
  "Language" text,
  "AuthToken" text,
  CONSTRAINT "PK_User" PRIMARY KEY ("Email")
)
WITH (
  OIDS=FALSE
);
