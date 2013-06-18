/* Chcem vedieť -- Slovak for "I want to know" -- a server to ease access to information under the
 * Slovak Freedom Of Information Act 211/2000 Coll. (http://www.urzd.sk/legislativa/211-00-en.pdf)
 * Slovak description: Infozákon pre lenivých -- pohodlné podávanie žiadostí o informácie
 * Umožňuje podať formálne správnu žiadosť, odsledovať celý proces, dostávať notifikácie o uplynutých lehotách a zdieľať informácie s ostatnými používateľmi.
 *
 * This project shall use (preferably) english terms as defined in the english translation above, such as
 *
 * Obligee - povinná osoba
 * Applicant - žiadateľ
 *
 * Legal information: [TODO: put this in a separate html, provide a public link]
*
 * Legal or practical information about FOIA process in Slovakia (in Slovak):
 *
 * (vzdy) aktualizovane znenie zakona na JASPI (kliknut na zelene Rek zákony):
 * http://jaspi.justice.gov.sk/jaspiw1/index_jaspi0.asp?MOD=html&FIR=demo&JEL=n&AGE=zak&TNU=y&IDC=211%2F2000
 *
 * wwwold.justice.sk/kop/pk/2005/pk05016_03.pdf - Správa ministra spravodlivosti, výklad niektorých aspektov infozákona
 * Velmi dolezite, hovori sa tu o tom, preco sa nema zakon obmedzovat (kvoli tzv. "sikanovaniu" uradnikov),
 * Miesto toho specifikuje, ako maju povinne osoby vyuzivat legalne moznosti: napr. povinna osoba nema povinnost vytvarat analyzy a pod.
 *
 * http://www.ivo.sk/buxus/docs/vyskum/subor/produkt_4146.pdf - Infozákon v praxi: právna analýza a názory verejnosti
 * http://www.changenet.sk/?section=howto&cat=80696&x=80695  - Právo na informácie - Sprievodca aktívneho občana
 * http://www.changenet.sk/?section=howto&x=80723&cat=80696 -  Právo na informácie - Sprievodca pracovníkov verejnej správy
 *
 * http://www.changenet.sk/?section=doc&x=81499&cat=80696  Rozsudok Krajského súdu v Bratislave 19 S 31/02 (A. L. vs. Univerzita Komenského v Bratislave)
 * (inštitút fiktívneho rozhodnutia nelegalizuje nečinnosť povinnej osoby, ale slúži na ochranu občana)
 *
 * http://www.changenet.sk/?section=doc&x=81502&cat=80696 - Rozsudok Najvyššieho súdu SR 7 Sž 180/01 (XXX s.r.o. vs. Ministerstvo dopravy, pôšt a telekomunikácií SR)
 * (povinné osoby musia vybaviť i opakovanú žiadosť o tú istú informáciu.)
 */


Obligees = new Meteor.Collection("obligees");

if (Meteor.isClient) {

var alternate_characters = {
	"a": "aáä",
	"c": "cč",
	"d": "dď",
	"e": "eéë",
	"i": "ií",
	"l": "lĺľ",
	"n": "nň",
	"o": "oóôöő",
	"r": "rŕř",
	"s": "sš",
	"t": "tť",
	"u": "uúüű",
	"y": "yý",
	"z": "zž",
};

//Session.set("filter","first");

  Template.listObligees.events({
    'keyup .fil': function () {
//      myfilter = template.find("fil").value;
      //Session.set("filter",document.getElementById("myfil").value());
//        Session.set("filter", template.find("fil").value);

        //Session.set("filter", Math.random());

        //Session.set("filter", $('.fil').val());
        //Session.set("filter", template.find("fil").value);

        var filter = document.getElementById("myfil").value;
	for(letter in alternate_characters)
	  filter=filter.replace(letter, "["+alternate_characters[letter]+"]");

	//var filter = $("input.fil").value;
        /*var filter = document.getElementById("myfil").value;
        var filter = document.getElementById("myfil").value;
        var filter = document.getElementById("myfil").value;*/
        Session.set("filter", filter);
	console.log(filter);
    }
  });

    Template.ziadost.events({
    'keyup .ziadane-informacie': function () {
        var ziadane_informacie = document.getElementById("ziadane-informacie").value;
        Session.set("ziadane_informacie", ziadane_informacie);
    }
  });


  Template.listObligees.filter = function() {
    return Session.get("filter");
  }

    Template.email.ziadane_informacie = function() {
    return Session.get("ziadane_informacie");
  }


  Template.listObligees.obligees = function () {
	var filter = Session.get("filter");
//	if(myfilter==null || myfilter==0 || myfilter=="" || myfilter.length==0)
	//myfilter=document.getElementById("myfil").value;
	if(filter==null || filter=="")
	{
	    return Obligees.find({}, {sort: {score: -1, name: 1}});
	}
	else {
	    return Obligees.find({name:{$regex:filter,  $options: 'i'}}, {sort: {score: -1, name: 1}});
	}

  };

  Template.listObligees.selected_name = function () {
    var obligee = Obligees.findOne(Session.get("selected_obligee"));
    return obligee && obligee.name;
  };

  Template.email.selected_name = Template.listObligees.selected_name;

  //Template.listObligees.filter = function() {return find(".filter").value;}

  Template.obligee.selected = function () {
    return Session.equals("selected_obligee", this._id) ? "selected" : '';
  };

  Template.listObligees.events({
    'click input.inc': function () {
      Obligees.update(Session.get("selected_obligee"), {$inc: {score: 1}});

      Meteor.call('sendEmail',
            'mmmaly@gmail.com',
            'inymail@chcemvediet.sk',
            'inymail@chcemvediet.sk',
            'Pokusna Ziadost 4',
            Session.get("ziadane_informacie"));

    }
  });

  Template.obligee.events({
    'click': function () {
      Session.set("selected_obligee", this._id);
    }
  });
}

// On server startup, create some obligees if the database is empty.
if (Meteor.isServer) {
  Meteor.startup(function () {

    process.env.MAIL_URL="smtp://ziadost%40chcemvediet.sk:censored@smtp.gmail.com:465";

    if (true) {
      var names = ["Ministerstvo hospodárstva Slovenskej republiky",
"Ministerstvo financií Slovenskej republiky",
"Ministerstvo dopravy, výstavby a regionálneho rozvoja Slovenskej republiky",
"Ministerstvo pôdohospodárstva a rozvoja vidieka Slovenskej republiky",
"Ministerstvo vnútra Slovenskej republiky",
"Ministerstvo obrany Slovenskej republiky",
"Ministerstvo spravodlivosti Slovenskej republiky",
"Ministerstvo zahraničných vecí a európskych záležitostí Slovenskej republiky",
"Ministerstvo práce, sociálnych vecí a rodiny Slovenskej republiky",
"Ministerstvo životného prostredia Slovenskej republiky",
"Ministerstvo školstva, vedy, výskumu a športu Slovenskej republiky",
"Ministerstvo kultúry Slovenskej republiky",
"Ministerstvo zdravotníctva Slovenskej republiky", ];
//      var names = ["prazdny zoznam", ];
      Obligees.remove({});
      for (var i = 0; i < names.length; i++)
        Obligees.insert({name: names[i], score: Math.floor(Random.fraction()*10)*5});
    }
  });

  Meteor.methods({
  sendEmail: function (to, from, replyTo, subject, text) {
    check([to, from, subject, text], [String]);

    // Let other method calls from the same client start running,
    // without waiting for the email sending to complete.
    this.unblock();

    Email.send({
      to: to,
      from: from,
      subject: subject,
      replyTo: replyTo,
      text: text
    });
  }

});
}
