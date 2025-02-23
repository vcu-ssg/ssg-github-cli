# ssg-github-cli

A python wrapper around pygithub.

I needed to rename student teams for CMSC408. There must be unique team names within
an organization.  Student teams selecting names from one semester might collide
with team names in a second semester.

This utility lists team names that fork a repo.  This allows me to find all
the teams that forked a specific assignment, then adjust the team names
to include the assignment.

This is a CLI tool using CLICK.
