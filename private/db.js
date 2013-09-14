var _ = require("underscore"),
    pg = require("pg"),
    Q = require("q");

exports.getUser = function(email) {
    return executeQuery('SELECT * FROM "User" WHERE "email"=$1', [email])
        .then(function (result) {
            return result.rows.length == 1 ? result.rows[0] : null;
        });
};

exports.getUserByAuthToken = function(authToken) {
    return executeQuery('SELECT * FROM "User" WHERE "authToken"=$1', [authToken])
        .then(function (result) {
            return result.rows.length == 1 ? result.rows[0] : null;
        });
};

exports.createUser = function(user) {
    return executeQuery('INSERT INTO "User"("email", "password", "firstName", "lastName", "street", "city", "zip", "authToken", "language") VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)',
        [user.email, user.password, user.firstName, user.lastName, user.street, user.city, user.zip, user.authToken, user.language || "sk"]);
};

exports.updateUser = function(user) {
    var query = 'UPDATE "User" SET ',
        params = [];

    _.keys(user).forEach(function (key) {
        params.push(user[key]);
        if (params.length > 1)
            query += ',';
        query += '"' + key +'" = $' + params.length;
    });

    return executeQuery(query, params);
};

exports.findObligees = function(term, limit) {
    var query = 'SELECT * FROM "Obligee" WHERE unaccent_string("name") ~* $1 OR unaccent_string("street") ~* $1 OR unaccent_string("city") ~* $1',
        params = [term];

    if (typeof limit == "number") {
        query += ' LIMIT $2';
        params.push(limit);
    }

    return executeQuery(query, params)
        .then(function (result) {
            return result.rows || [];
        });
}


function executeQuery(command, params) {

    var deferred = Q.defer();

    pg.connect(process.env.DATABASE_URL, function (err, client, done) {
        if (err) return deferred.reject(new Error(err));

        client.query(command, params, function (err, result) {
            done();
            if (err) return deferred.reject(new Error(err));
            deferred.resolve(result);
        });
    });

    return deferred.promise;
}