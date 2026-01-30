from database.mongodb import mongodb

class PartnerRepository:
    def __init__(self):
        self.collection = mongodb.get_collection("partners")

    async def find_all(self):
        partners = []
        cursor = self.collection.find({})
        async for document in cursor:
            document["_id"] = str(document["_id"])
            partners.append(document)
        return partners