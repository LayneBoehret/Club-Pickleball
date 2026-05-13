[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/F1hjDb63)

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


## AI Usage

We used various AI tools throughout this project: **Claude**, **Cursor**, **Gemini**, and **ChatGPT**

The most common use case was debugging errors i.e. feeding server logs or screenshots of features not working and asking why a certain feature didn't work how it should have and getting pointed to the right area of code that was causing the issue. We also used AI to help connect to external services like how to configure S3 with Django and Heroku and setting up Google OAuth with djagno-allauth, and provisioning everything on Heroku's end correctly. 

The main usecase of AI was using Cursor for the UI work. Once we had a base template of all our different tabs and our basic features working on those sections, we gave cursor a preexisting color scheme we decided on and a sketch drawn up on how we wanted each of the views to look and asked to clean it up. So that we could get the cleanliness of a consistent and clean styling across all the views and could focus our effort on actual features for our application.

In all cases the features, architecture, and decisions were built first. AI was brought in after the fact to fix what was broken or clean up what was already there.
