const dbBuilder = require("@airplanegobrr/database")
const express = require("express")
const hbs = require('express-hbs')
const bodyParser = require('body-parser')
const utils = require("../utils")
const fs = require("fs")
const path = require("path")
const app = express()
// This will only store the database IDs, and where they are
const db = new dbBuilder({filename: "aiCDN/database.json"})

app.set('views', path.join(__dirname, '/views'));
app.engine('hbs', hbs.express3())
app.set('view engine', 'hbs');

app.use(bodyParser.json({ limit: "100mb" }));
app.use(bodyParser.urlencoded({ extended: true }));

app.get("/", (req, res)=>{
    res.render("main")
})

const cacheDir = 'aiCDN/cache'

app.post("/upload/database", async(req, res)=>{
    var data = req.body ?? {
        databaseID: "ID",
        database: {
            //bla bla bal
        }
    }
    fs.mkdirSync(`${cacheDir}/${data.databaseID}/img`, {recursive: true})
    fs.writeFileSync(`${cacheDir}/${data.databaseID}/database.json`, JSON.stringify(data.database))
    res.json({
        good: true
    })
})

app.post("/upload/files", (req, res)=>{
    // req.body will have 10 images under req.body.images
    var data = req.body ?? {
        images: {name: "data"},
        folder: "username",
        databaseID: "xyz"
    }
    if (data && data.images && data.folder) {
        console.log(`Got img data!`, data.folder, data.databaseID)
        for (var img in data.images){
            var imgB64Data = data.images[img]
            var imgBuffer = Buffer.from(imgB64Data, "base64")
            fs.mkdirSync(`${cacheDir}/${data.databaseID}/img/${data.folder}`, {recursive: true})
            fs.writeFileSync(`${cacheDir}/${data.databaseID}/img/${data.folder}/${img}`, imgBuffer)
        }
        res.json({
            good: true
        })
    }
})


app.post("/upload/check", (req, res)=>{
    var data = req.body ?? {
        imgStr: "apgb-p-t/5cff9f2f-2a99-4197-a577-a2b47f8ccb63-4.png",
        databaseID: "xyz" //Not required
    }
    if (data.databaseID) {
        if (fs.existsSync(`${cacheDir}/${data.databaseID}`)){
            const imgSplit = data.imgStr.split("/")
            // console.log(imgSplit)
            if (fs.existsSync(`${cacheDir}/${data.databaseID}/${imgSplit[0]}`)){
                if (fs.existsSync(`${cacheDir}/${data.databaseID}/${imgSplit[0]}/${imgSplit[1]}`)){
                    // console.log("Found")
                    return res.json({
                        found: true
                    })
                // Found folder
                }
            } else {
                // Go in all folders
                const folders = fs.readdirSync(`${cacheDir}/${data.databaseID}`)
                for (var folder of folders){
                    if (fs.existsSync(`${cacheDir}/${data.databaseID}/${folder}/${imgSplit[0]}`)){
                        // console.log("Found")
                        return res.json({
                            found: true,
                            folder
                        })
                    }
                }
            }
        }
    } else {
        console.log(data)
    }
    return res.json({
        found: false
    })
})

app.listen(3505, () => {
    console.log("Running http://localhost:3505")
})