CREATE TABLE "User"
(
  "email" text NOT NULL,
  "password" text NOT NULL,
  "firstName" text,
  "lastName" text,
  "street" text,
  "city" text,
  "zip" text,
  "language" text,
  "authToken" text,
  CONSTRAINT "PK_User" PRIMARY KEY ("email")
)
WITH (
  OIDS=FALSE
);
