#user config helper class
class UserConfig():
    def __init__(self, bot, user_id) -> None:
        self.user_id = self.sanitize(user_id)
        print(user_id)
        self.database = bot.database
        self.config = {}
    async def loadconfig(self):
        self.config = await self.database.get_config(self.user_id)
    def get(self, key):
        key = self.sanitize(key)
        #get the value of a key from the config
        data = self.config.get(key)
        if data == None:
            return ""
        return data
        pass
    async def set(self, key, value):
        key = self.sanitize(key)
        if value != None: #do nothing if value is none
            value = self.sanitize(value)
            #set the value of a key in the config
            self.config[key] = value
            await self.save()
        
    async def save(self):
        await self.database.store_config(self.user_id, self.config)
    async def saveToSlot(self, slot):
        slot = self.sanitize(slot)
        await self.database.save_config(self.user_id, slot, self.config)
    async def loadFromSlot(self, slot):
        slot = self.sanitize(slot)
        self.config = await self.database.get_saved_config(self.user_id, slot)
        await self.save()
        #load the config from a slot
        pass
    async def listSlots(self):
        #list the slots
        slots = await self.database.get_config_list(self.user_id)
        out = ""
        for slot in slots:
            out += f"**{slot[0]}**\n"
            e = eval(slot[1])
            for key in e:
                out += f"{key}: {e[key]}\n"
        return out
    async def deleteSlot(self, slot):
        slot = self.sanitize(slot)
        #delete a slot
        pass
    #default config
    async def default(self):
        await self.loadconfig()
        await self.saveToSlot("last")
        self.config = {}
        await self.save()
    #sanitizer
    def sanitize(self, input):
        return input
    #tostring method
    def __str__(self):
        config_string = ""
        for key in self.config:
                config_string += f"{key}: {self.config[key]}\n"
        return config_string
        pass
    