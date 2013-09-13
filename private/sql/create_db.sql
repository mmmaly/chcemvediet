CREATE TABLE "User"
(
  "id" serial NOT NULL,
  "email" text NOT NULL,
  "password" text,
  "firstName" text,
  "lastName" text,
  "street" text,
  "city" text,
  "zip" text,
  "language" text,
  "authToken" text,
  CONSTRAINT "PK_User" PRIMARY KEY ("id")
)
WITH (
  OIDS=FALSE
);
