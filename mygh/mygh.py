"""
"""
import os
import json
import click
from github import Github
import subprocess

CACHE_FILE = "team_repo_access.json"

@click.group()
def cli():
    """A CLI tool for managing GitHub teams."""
    pass

@click.command()
@click.argument("name")
def greet(name):
    """Greets the user."""
    click.echo(f"Hello, {name}!")

@click.command()
@click.option("--org", default="cmsc-vcu", help="GitHub organization name")
def list_teams(org):
    """Lists all teams in the specified GitHub organization."""
    try:
        # Fetch the GitHub token using gh CLI
        token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
        
        if not token:
            click.echo("Error: No GitHub token found. Run 'gh auth login' to authenticate.", err=True)
            return
        
        g = Github(token)
        org_obj = g.get_organization(org)
        teams = org_obj.get_teams()

        click.echo(f"Teams in {org}:")
        for team in teams:
            click.echo(f"- {team.name} (ID: {team.id})")
    except subprocess.CalledProcessError:
        click.echo("Error: Failed to retrieve GitHub token. Ensure 'gh' is installed and authenticated.", err=True)
    except Exception as e:
        click.echo(f"Error fetching teams: {e}", err=True)

@click.command()
@click.option("--org", default="cmsc-vcu", help="GitHub organization name")
@click.option("--repo", required=True, help="Repository name to check forks for")
def list_fork_teams(org, repo):
    """Lists all teams that have forked a given repository."""
    try:
        # Retrieve the GitHub token from `gh auth token`
        token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
        if not token:
            click.echo("Error: No GitHub token found. Run 'gh auth login' to authenticate.", err=True)
            return

        g = Github(token)
        repo_full_name = f"{org}/{repo}"  # Construct full repo name (e.g., cmsc-vcu/repo-name)
        repository = g.get_repo(repo_full_name)

        forks = repository.get_forks()
        if forks.totalCount == 0:
            click.echo(f"No forks found for {repo_full_name}.")
            return

        click.echo(f"Forks of {repo_full_name}:")

        # Get the teams of the organization
        org_obj = g.get_organization(org)
        teams = {team.id: team.name for team in org_obj.get_teams()}

        for fork in forks:
            fork_owner = fork.owner
            fork_owner_type = fork_owner.type  # "User" or "Organization"

            if fork_owner_type == "Organization":
                fork_org = g.get_organization(fork_owner.login)
                fork_teams = fork_org.get_teams()
                for team in fork_teams:
                    if team.id in teams:
                        click.echo(f"- {team.name} (Owned by {fork_owner.login})")
            else:
                click.echo(f"- {fork_owner.login} (Personal fork)")

    except subprocess.CalledProcessError:
        click.echo("Error: Failed to retrieve GitHub token. Ensure 'gh' is installed and authenticated.", err=True)
    except Exception as e:
        click.echo(f"Error fetching forks: {e}", err=True)

@click.command()
@click.option("--org", default="cmsc-vcu", help="GitHub organization name")
@click.option("--repo", required=True, help="Repository name to check forks for")
def list_forks(org, repo):
    """Lists all forked repositories for the given parent repository."""
    try:
        # Retrieve the GitHub token from `gh auth token`
        token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
        if not token:
            click.echo("Error: No GitHub token found. Run 'gh auth login' to authenticate.", err=True)
            return

        g = Github(token)
        repo_full_name = f"{org}/{repo}"  # Construct full repo name (e.g., cmsc-vcu/repo-name)
        repository = g.get_repo(repo_full_name)

        forks = repository.get_forks()
        if forks.totalCount == 0:
            click.echo(f"No forks found for {repo_full_name}.")
            return

        click.echo(f"Forked Repositories for {repo_full_name}:")

        for fork in forks:
            fork_owner = fork.owner.login  # The user or organization that owns the fork
            fork_repo_name = fork.full_name  # The full repo name (e.g., owner/repo)
            click.echo(f"- {fork_repo_name} (Owned by {fork_owner})")

    except subprocess.CalledProcessError:
        click.echo("Error: Failed to retrieve GitHub token. Ensure 'gh' is installed and authenticated.", err=True)
    except Exception as e:
        click.echo(f"Error fetching forks: {e}", err=True)


@click.command()
@click.option("--org", default="cmsc-vcu", help="GitHub organization name")
@click.option("--repo", required=True, help="Repository name (without org) to check team access")
def check_team_access(org, repo):
    """Checks which teams have access to a given repository."""
    try:
        # Retrieve the GitHub token from `gh auth token`
        token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
        if not token:
            click.echo("Error: No GitHub token found. Run 'gh auth login' to authenticate.", err=True)
            return

        g = Github(token)
        org_obj = g.get_organization(org)
        repo_full_name = f"{org}/{repo}"
        repository = g.get_repo(repo_full_name)

        click.echo(f"Checking team access for repository: {repo_full_name}...")

        teams_with_access = []

        for team in org_obj.get_teams():
            try:
                # Check if the team has access to the repository
                permission = team.get_repo_permission(repository)
                if permission:
                    teams_with_access.append(f"- {team.name} (Permission: {permission})")
            except:
                pass  # If a team doesn't have access, an exception occurs (so we skip it)

        if teams_with_access:
            click.echo("Teams with access:")
            for team_info in teams_with_access:
                click.echo(team_info)
        else:
            click.echo("No teams have access to this repository.")

    except subprocess.CalledProcessError:
        click.echo("Error: Failed to retrieve GitHub token. Ensure 'gh' is installed and authenticated.", err=True)
    except Exception as e:
        click.echo(f"Error checking team access: {e}", err=True)

def get_github_token():
    """Retrieve GitHub token using 'gh auth token'."""
    try:
        token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
        if not token:
            raise Exception("No GitHub token found. Run 'gh auth login' to authenticate.")
        return token
    except subprocess.CalledProcessError:
        raise Exception("Error retrieving GitHub token. Ensure 'gh' is installed and authenticated.")

def cache_team_repo_access(org):
    """Fetch and cache team-repo permissions for the organization."""
    token = get_github_token()
    g = Github(token)
    org_obj = g.get_organization(org)

    team_repo_access = {}  # Dictionary: { team_name: [repo1, repo2, ...] }

    click.echo(f"Fetching all team-repo permissions for {org}. This may take a while...")

    for team in org_obj.get_teams():
        team_name = team.name
        repos = []
        try:
            for repo in team.get_repos():
                repos.append(repo.name)  # Store only repo name (not full path)
        except:
            continue  # Skip if there's an issue accessing repo permissions

        if repos:
            team_repo_access[team_name] = repos

    # Save to JSON file
    with open(CACHE_FILE, "w") as f:
        json.dump(team_repo_access, f, indent=4)

    click.echo(f"Cached team-repo access data to {CACHE_FILE}")

@click.command()
@click.option("--org", default="cmsc-vcu", help="GitHub organization name")
def update_cache(org):
    """Updates the team-repo access cache."""
    cache_team_repo_access(org)

@click.command()
@click.option("--repo", required=True, help="Repository name (without org) to check team access")
def check_team_access_fast(repo):
    """Check which teams have access to a given repository using cached data."""
    if not os.path.exists(CACHE_FILE):
        click.echo("Error: Cache file not found. Run 'poetry run mygh update-cache' first.")
        return

    with open(CACHE_FILE, "r") as f:
        team_repo_access = json.load(f)

    teams_with_access = [team for team, repos in team_repo_access.items() if repo in repos]

    if teams_with_access:
        click.echo(f"Teams with access to {repo}:")
        for team in teams_with_access:
            click.echo(f"- {team}")
    else:
        click.echo(f"No teams have access to {repo}.")

@click.command()
@click.option("--org", default="cmsc-vcu", help="GitHub organization name")
@click.option("--repo", required=True, help="Repository name to check forks for")
@click.option("--append-team-name-with", default="", help="Text to append to each team name")
@click.option("--confirm", is_flag=True, help="If set, rename the teams instead of listing changes")
def list_fork_teams_fast(org, repo, append_team_name_with, confirm):
    """Lists all teams with access to forks of the given repository using cached data.
    If --confirm is set, actually renames the teams.
    Without --append-team-name-with, lists only the repo name and team name.
    """

    if not os.path.exists(CACHE_FILE):
        click.echo("Error: Cache file not found. Run 'poetry run mygh update-cache' first.")
        return

    # Load team-repo cache
    with open(CACHE_FILE, "r") as f:
        team_repo_access = json.load(f)

    try:
        token = get_github_token()
        g = Github(token)
        repo_full_name = f"{org}/{repo}"
        repository = g.get_repo(repo_full_name)

        forks = repository.get_forks()
        if forks.totalCount == 0:
            click.echo(f"No forks found for {repo_full_name}.")
            return

        click.echo(f"Forks of {repo_full_name}:")

        fork_teams = {}

        org_obj = g.get_organization(org)
        existing_teams = {team.name: team for team in org_obj.get_teams()}  # Map current teams

        for fork in forks:
            fork_repo_name = fork.name  # Only the repo name, not full path
            fork_owner = fork.owner.login  # The user or org that owns the fork

            teams_with_access = [
                team for team, repos in team_repo_access.items() if fork_repo_name in repos
            ]

            if teams_with_access:
                fork_teams[fork_repo_name] = teams_with_access

        if not fork_teams:
            click.echo("No teams found with access to the forks.")
            return

        if append_team_name_with:
            click.echo("Proposed Team Name Changes:")
        else:
            click.echo("Repository - Team Name List:")

        for fork, teams in fork_teams.items():
            for team in teams:
                if append_team_name_with:
                    new_team_name = f"{team}-{append_team_name_with}"
                    # Check if the team already has the suffix
                    if team.endswith(f"-{append_team_name_with}"):
                        click.echo(f"- {team} → {new_team_name} (Already named correctly, no rename needed)")
                        continue  # Skip renaming if already correct
                    click.echo(f"- {team} → {new_team_name}")

                    if confirm:
                        if team in existing_teams:
                            try:
                                existing_teams[team].edit(name=new_team_name)
                                click.echo(f"✅ Renamed {team} to {new_team_name}")
                            except Exception as e:
                                click.echo(f"❌ Failed to rename {team}: {e}", err=True)
                        else:
                            click.echo(f"⚠️ Team {team} not found in the organization.")
                else:
                    click.echo(f"- {fork} - {team}")  # Simple repo-team listing

        if not confirm and append_team_name_with:
            click.echo("\n🚀 Run the command again with '--confirm' to apply changes.")

    except subprocess.CalledProcessError:
        click.echo("Error: Failed to retrieve GitHub token. Ensure 'gh' is installed and authenticated.", err=True)
    except Exception as e:
        click.echo(f"Error fetching forks: {e}", err=True)



cli.add_command(greet)
cli.add_command(list_teams)
cli.add_command(list_fork_teams)
cli.add_command(list_forks)
cli.add_command(check_team_access)

cli.add_command(update_cache)
cli.add_command(check_team_access_fast)
cli.add_command(list_fork_teams_fast)



if __name__ == "__main__":
    cli()




