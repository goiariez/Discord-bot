import discord
from discord.ext import commands
import sqlite3
import disnake
from disnake.ext import commands
from discord.ext import commands
from tabulate import tabulate
import json

conn = sqlite3.connect("Discord.db")
cursor = conn.cursor()
bot = commands.Bot(command_prefix="!", help_command=None, intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot was connected to the server")
    for guild in bot.guilds:
        print(guild.id)
        serv = guild
        for member in guild.members:
            cursor.execute(f"SELECT id FROM users where id={member.id}")
            if cursor.fetchone() == None:
                cursor.execute(
                    f"INSERT INTO users VALUES ({member.id}, '{member.name}', '<@{member.id}>', 50000, 'S','[]',0,0)")
            else:
                pass
            conn.commit()
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("help"))


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    msg = message.content.lower()
    greeting_words = ["hello", "hi", "привет"]
    censored_words = ["дурак", "дура", "придурок"]

    if msg in greeting_words:
        await message.channel.send(f"{message.author.name}, приветствую тебя!")

    # Filter censored words
    for bad_content in msg.split(" "):
        if bad_content in censored_words:
            await message.channel.send(f"{message.author.mention}, ай-ай-ай... Плохо, плохо, так нельзя!")
    if len(message.content) > 10:
        for row in cursor.execute(f"SELECT xp,lvl,money FROM users where id={message.author.id}"):
            expi = row[0] + random.randint(5, 40)
            cursor.execute(f'UPDATE users SET xp={expi} where id={message.author.id}')
            lvch = expi / (row[1] * 1000)
            print(int(lvch))
            lv = int(lvch)
            if row[1] < lv:
                await message.channel.send(f'Новый уровень!')
                bal = 1000 * lv
                cursor.execute(
                    f'UPDATE users SET lvl={lv},money={bal} where id={message.author.id}')
    await bot.process_commands(message)
    conn.commit()


@bot.command()
async def account(ctx):
    table = [["nickname", "money", "lvl", "xp"]]
    for row in cursor.execute(f"SELECT nickname,money,lvl,xp FROM users where id={ctx.author.id}"):
        table.append([row[0], row[1], row[2], row[3]])
        await ctx.send(f">\n{tabulate(table)}")


@bot.command()
async def inventory(ctx):
    counter = 0
    for row in cursor.execute(f"SELECT inventory FROM users where id={ctx.author.id}"):
        data = json.loads(row[0])
        table = [["id", "type", "name"]]
        for row in data:
            prt = row
            for row in cursor.execute(f"SELECT id,type,name FROM shop where id={prt}"):
                counter += 1
                table.append([row[0], row[1], row[2]])

                if counter == len(data):
                    await ctx.send(f'>\n{tabulate(table)}')


@bot.command()
async def shop(ctx):
    counter = 0
    table = [["id", "type", "name", "cost"]]
    for row in cursor.execute(f"SELECT id,type,name,cost FROM shop"):
        counter += 1
        table.append([row[0], row[1], row[2], row[3]])
        if counter == 4:
            await ctx.send(f'>\n{tabulate(table)}')


@bot.event
async def on_member_join(member):
    channel = bot.get_channel()
    role = discord.utils.get(member.guild.roles, id=role_id)

    await member.add_roles(role)
    cursor.execute(f"SELECT id FROM users where id={member.id}")
    if cursor.fetchone() == None:
        cursor.execute(
            f"INSERT INTO users VALUES ({member.id}, '{member.name}', '<@{member.id}>', 50000, 'S','[]',0,0)")
    else:
        pass
    conn.commit()


async def buy(ctx, a: int):
    uid = ctx.author.id
    await ctx.send('Обработка... Если ответа не последует, указан неверный id предмета [buy {id}]')
    for row in cursor.execute(f"SELECT money FROM users where id={uid}"):
        money = row[0]
        for row in cursor.execute(f"SELECT id,name,cost FROM shop where id={a}"):
            cost = row[2]
            if money >= cost:
                money -= cost
                await ctx.send(f'Вы приобрели "{row[1]}" за {row[2]}')

                for row in cursor.execute(f"SELECT inventory FROM users where id={uid}"):
                    data = json.loads(row[0])
                    data.append(a)
                    daed = json.dumps(data)
                    cursor.execute('UPDATE users SET money=?,inventory = ? where id=?',
                                   (money, daed, uid))
                    pass
            if money < cost:
                await ctx.send(f'Недостаточно средств')
                pass
    conn.commit()


@bot.event
async def on_command_error(ctx, error):
    print(error)

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"{ctx.author}, у вас недостаточно прав для выполнения данной команды!")
    elif isinstance(error, commands.UserInputError):
        await ctx.send(embed=discord.Embed(
            description=f"Правильное использование команды: `{ctx.prefix}{ctx.command.name}` ({ctx.command.brief})\nExample: {ctx.prefix}{ctx.command.usage}"
        ))


@bot.command(name="очистить", brief="Очистить чат от сообщений, по умолчанию 10 сообщений", usage="clear <amount=10>")
async def clear(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"Was deleted {amount} messages...")


@bot.command(name="кик", brief="Выгнать пользователя с сервера", usage="kick <@user> <reason=None>")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await ctx.message.delete(delay=1)

    await member.send(f"You was kicked from server")
    await ctx.send(f"Member {member.mention} was kicked from this server!")
    await member.kick(reason=reason)


@bot.command(name="бан", brief="Забанить пользователя на сервере", usage="ban <@user> <reason=None>")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.send(f"You was banned on server")
    await ctx.send(f"Member {member.mention} was banned on this server")
    await member.ban(reason=reason)


@bot.command(name="разбанить", brief="Разбанить пользователя на сервере", usage="unban <user_id>")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)


@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="Help menu",
        description="Here you can find the necessary command"
    )
    commands_list = ["clear", "kick", "ban", "unban"]
    descriptions_for_commands = ["Clear chat", "Kick user", "Ban user", "Unban user"]

    for command_name, description_command in zip(commands_list, descriptions_for_commands):
        embed.add_field(
            name=command_name,
            value=description_command,
            inline=False
        )

    await ctx.send(embed=embed)


@bot.command(name="мут", brief="Запретить пользователю писать (настройте роль и канал)", usage="mute <member>")
async def mute_user(ctx, member: discord.Member):
    mute_role = discord.utils.get(ctx.message.guild.roles, name="role name")

    await member.add_roles(mute_role)
    await ctx.send(f"{ctx.author} gave role mute to {member}")


@bot.command(name="join", brief="Подключение к голосовому каналу", usage="join")
async def join_to_channel(ctx):
    global voice
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    channel = ctx.message.author.voice.channel

    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
        await ctx.send(f"Bot was connected to the voice channel")


@bot.command(name="leave", brief="Отключение от голосового канала", usage="leave")
async def leave_from_channel(ctx):
    global voice
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    channel = ctx.message.author.voice.channel

    if voice and voice.is_connected():
        await voice.disconnect()
    else:
        voice = await channel.disconnect()
        await ctx.send(f"Bot was connected to the voice channel")


bot.run("TOKEN")
