
const dbBuilder = require("@airplanegobrr/database")
const db = new dbBuilder({filename:"aiServer/database.json"})

async function main(){
    await db.load()
    console.log(await db.get(""))
}
main()