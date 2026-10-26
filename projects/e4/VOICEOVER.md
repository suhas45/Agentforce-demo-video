# E4-1 · Shared / Generic Email on Lead and Contact — Voiceover

**Intro**
1. Some customers share one email address between several people, like a QC team that uses a single inbox.
2. Today, Salesforce blocks the second contact as a duplicate. And lead conversion can link a lead to the wrong person, because it matches on email.
3. So, Conscendo added a Shared / Generic Email flag on Lead and Contact.
4. When it's ticked, duplicate checks and conversion ignore the email, and match people by mobile number and name instead.

**Demo (screen recording)**
5. Here's a lead, Mr. Sai Suhas, with the Shared / Generic Email checkbox ticked.
6. The user converts the lead. Since the email is shared, conversion looks for an existing contact on the account by mobile and name, never by email.
7. No contact on the account matches this mobile and name, so a new contact is created, and the lead converts successfully.
8. The new opportunity is created on the Conscendo account.
9. On the account, the new contact Sai Suhas now appears. Two other contacts here share the same email address, and both were saved without being blocked as duplicates.

**Close**
10. With the flag ticked, contacts on the same account can share an email, as long as their mobile or name is different.
11. Real duplicates are still blocked: the same mobile and the same name, on the same account.
12. Leads and contacts without the flag work exactly as before.
13. Conscendo. Igniting Growth.
