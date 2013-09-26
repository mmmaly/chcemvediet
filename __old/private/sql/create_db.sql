-- TODO: find a way to set this to the current directory (or from outside)
SET @importPath = '/Users/tomas/Documents/node/chcemvediet/private/sql';

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

CREATE TABLE "Obligee"
(
  "id" serial NOT NULL,
  "email" text NOT NULL,
  "name" text,
  "street" text,
  "city" text,
  "zip" text,
  CONSTRAINT "PK_Obligee" PRIMARY KEY ("id")
)
WITH (
  OIDS=FALSE
);

SET @obligeesFile = @importPath + '/listObligees.csv';
COPY "Obligee"("name","street","city","zip","email") FROM '@obligeesFile' DELIMITER ',' CSV HEADER;

-- TODO: this is quite lame but I haven't found any better way.. is there one ?
CREATE OR REPLACE FUNCTION unaccent_string(text)
RETURNS text
IMMUTABLE
STRICT
LANGUAGE SQL
AS $$
SELECT translate(
    $1,
    'áäéíóöúüÁÄÉÍÓÖÚÜčďĺľňŕřšťýžČĎĹĽŇŔŘŠŤÝŽ',
    'aaeioouuAAEIOOUUcdllnrrstyzCDLLNRRSTYZ'
);
$$;