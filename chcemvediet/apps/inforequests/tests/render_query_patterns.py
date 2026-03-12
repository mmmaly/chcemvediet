from poleno.utils.misc import squeeze


base = [
    u'FROM "accounts_profile" WHERE "accounts_profile"."user_id" = %s',
    squeeze(u"""
        SELECT COUNT\(\*\)( AS "__count")? FROM "mail_message"
        INNER JOIN "inforequests_inforequestemail" ON \( "mail_message"."id" = "inforequests_inforequestemail"."email_id" \)
        INNER JOIN "inforequests_inforequest" ON \( "inforequests_inforequestemail"."inforequest_id" = "inforequests_inforequest"."id" \)
        WHERE \("inforequests_inforequestemail"."type" = %s
            AND "inforequests_inforequest"."applicant_id" = %s
            AND "inforequests_inforequest"."closed" = %s\)
        """),
    u'FROM "invitations_invitationsupply" WHERE "invitations_invitationsupply"."user_id" = %s',
]
