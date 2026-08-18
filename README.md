# Project B-08 — UVA Pickleball

A club management platform built for UVA Pickleball. Supports real-time chat, announcements, event scheduling, document storage, and role-based access control.

---

## Using the App 

Here's how a typical UVA Pickleball Club would use it.

### Member
A new player joins the club and signs in with their Google account. They start on the member dashboard where they can view club announcements, check upcoming events, browse shared documents like the club roster or waiver form, and chat with other members in the general chat room. They can edit their own profile with a photo and birthday.

### Club Leader (Officers/Executives)
The club's president or a designated officer signs in and lands on a similar dashboard to members where they see a quick glance at announcements and upcoming events. From here they are given additional functionality on each of the extra tabs. They can post announcements under the announcements tab, create events on the calendar tab, upload documents to S3 on the Documents tab and they have an extra tab labeled "Admin Chat". Officers are promoted to this role using a User Administrator account.

### User Administrator
The president is given a User Administrator by a developer via the Django shell (this role cannot be assigned through the app). The sole purpose within the app is that this account will be able to view all users and promote or demote members to Club Leader. They cannot access any other features like announcements or documents, keeping their scope intentionally limited. The Club President should be the only one with access to this account (or a select few members) but all should have other normal accounts to interface with the software.
