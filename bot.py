import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import random
import os

# -------------------- Intents --------------------
# Using only default intents - no privileged intents needed
intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

# -------------------- Data Handling --------------------
FILENAME = os.path.join(os.path.dirname(__file__), "tournament.json")

tournament = {
    "name": None,
    "players": [],
    "matches": [],
    "started": False
}

def save_data():
    try:
        with open(FILENAME, "w") as f:
            json.dump(tournament, f)
    except Exception as e:
        print("Error saving tournament.json:", e)

def load_data():
    global tournament
    try:
        if not os.path.exists(FILENAME):
            with open(FILENAME, "w") as f:
                json.dump(tournament, f)
        else:
            with open(FILENAME, "r") as f:
                tournament = json.load(f)
    except Exception as e:
        print("Error loading tournament.json:", e)

load_data()

# -------------------- /create Command --------------------
@tree.command(name="create", description="Create a new tournament")
async def create(interaction: discord.Interaction, name: str):
    tournament["name"] = name
    tournament["players"] = []
    tournament["matches"] = []
    tournament["started"] = False
    save_data()
    await interaction.response.send_message(f"??? Tournament **{name}** created! Use /panel to manage it.")

# -------------------- /panel Command --------------------
@tree.command(name="panel", description="Show tournament buttons")
async def panel(interaction: discord.Interaction):
    if not tournament["name"]:
        await interaction.response.send_message("No tournament exists. Use /create first!", ephemeral=True)
        return

    view = View()

    # Join Button
    join_button = Button(label="Join Tournament", style=discord.ButtonStyle.green)
    async def join_callback(button_interaction: discord.Interaction):
        user_id = button_interaction.user.id
        if tournament["started"]:
            await button_interaction.response.send_message("Tournament already started!", ephemeral=True)
            return
        if user_id in tournament["players"]:
            await button_interaction.response.send_message("You already joined!", ephemeral=True)
            return
        tournament["players"].append(user_id)
        save_data()
        await button_interaction.response.send_message(f"? <@{user_id}> joined!", ephemeral=True)
    join_button.callback = join_callback
    view.add_item(join_button)

    # Start Button (Admin Only)
    start_button = Button(label="Start Tournament", style=discord.ButtonStyle.blurple)
    async def start_callback(button_interaction: discord.Interaction):
        if not button_interaction.user.guild_permissions.administrator:
            await button_interaction.response.send_message("Only admins can start the tournament!", ephemeral=True)
            return
        if len(tournament["players"]) < 2:
            await button_interaction.response.send_message("Not enough players!", ephemeral=True)
            return

        # 1v1 pairing
        random.shuffle(tournament["players"])
        matches = []
        for i in range(0, len(tournament["players"]), 2):
            if i + 1 < len(tournament["players"]):
                matches.append([tournament["players"][i], tournament["players"][i+1]])
            else:
                matches.append([tournament["players"][i]])  # bye for odd player
        tournament["matches"] = matches
        tournament["started"] = True
        save_data()

        msg = "??? **Round 1 Matches:**\n"
        for match in matches:
            if len(match) == 2:
                msg += f"<@{match[0]}> vs <@{match[1]}>\n"
            else:
                msg += f"<@{match[0]}> gets a bye\n"
        await button_interaction.response.send_message(msg)
    start_button.callback = start_callback
    view.add_item(start_button)

    # Report Win Button
    report_button = Button(label="Report Match Win", style=discord.ButtonStyle.red)
    async def report_callback(button_interaction: discord.Interaction):
        if not tournament["started"]:
            await button_interaction.response.send_message("Tournament has not started yet!", ephemeral=True)
            return
        user_id = button_interaction.user.id
        won_match = None
        for match in tournament["matches"]:
            if user_id in match:
                won_match = match
                break
        if not won_match:
            await button_interaction.response.send_message("You are not in a current match!", ephemeral=True)
            return

        # Advance winner
        tournament["players"] = [user_id]
        tournament["matches"] = []
        tournament["started"] = False
        save_data()
        await button_interaction.response.send_message(f"?? <@{user_id}> wins the tournament!", ephemeral=False)
    report_button.callback = report_callback
    view.add_item(report_button)

    # View Players Button
    view_players_button = Button(label="View Players", style=discord.ButtonStyle.gray)
    async def view_players_callback(button_interaction: discord.Interaction):
        if not tournament["name"]:
            await button_interaction.response.send_message("No tournament exists.", ephemeral=True)
            return
        num_players = len(tournament["players"])
        if num_players == 0:
            await button_interaction.response.send_message("No players have joined yet.", ephemeral=True)
            return
        player_list = "\n".join([f"<@{p}>" for p in tournament["players"]])
        await button_interaction.response.send_message(
            f"??? Tournament **{tournament['name']}** has **{num_players}** players signed up:\n{player_list}",
            ephemeral=True
        )
    view_players_button.callback = view_players_callback
    view.add_item(view_players_button)

    # Send Panel
    await interaction.response.send_message(f"??? **Tournament Panel for {tournament['name']}**", view=view)

# Bot Ready
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await tree.sync()

# Run Bot

client.run("MTQ3NDAzNjc4NzI3NjkzOTM5Nw.Gpcqia.ruEjmMgXjEGy4q79MXO2J1xMmpe4fMnUfmsHec")