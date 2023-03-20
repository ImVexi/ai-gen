const dbBuilder = require("@airplanegobrr/database")
const express = require("express")
const bodyParser = require('body-parser')
const utils = require("./utils")
const fs = require("fs")
const path = require("path")
const app = express()
const db = new dbBuilder()

const worker_api = express.Router()

worker_api.get("/get", async (req, res)=>{
    const line = await db.get(`line`)
    if (!line) return res.json({ready: false})
    const next = line.shift()
    if (next){
        await db.set("line", line)
        const lineData = await db.get(`inLine`)
        const nextData = lineData[next]
        delete lineData[next].status
        // delete lineData[next]
        // console.log(next, nextData)
        res.json({
            jobID: next,
            prompt: nextData.prompt,
            model: nextData.model,
            sample: nextData.sample
        })
    } else {
        return res.json({ready: false})
    }
})

worker_api.post("/done/:id", async (req, res)=>{
    // console.log(req.body)
    if (req.body && req.body.image) {
        const data = await db.get(`inLine.${req.params.id}`)
        data.status = "FINISHED"
        await db.set(`inLine.${req.params.id}`, data)
        var imgb64 = Buffer.from(req.body.image, "base64")
        var dir = `imgs/${data.username}`
        if (!fs.existsSync(dir)){
            fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(`${dir}/${req.params.id}.png`, imgb64)
    }
    res.send("ok.")
})

app.use(bodyParser.json({
    limit: "5mb"
}))
app.use(bodyParser.urlencoded({ extended: false }))
app.use("/worker", worker_api)

app.use((req, res, next)=>{
    var ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress 
    console.log(`${ip} ${decodeURI(req.url)}`)
    next()
})

app.get("/", (req, res)=>{
    res.sendFile(__dirname+"/index.html")
})

app.get("/queue/:id", async (req, res)=>{
    //console.log(req.params.id)
    const lineData = await db.get(`inLine.${req.params.id}`)
    const line = await db.get("line")
    res.json({
        status: lineData?.status ?? "N/A",
        id: req.params.id,
        position: line.indexOf(req.params.id)+1,
        username: lineData.username
    })
})

app.get("/generate", async (req, res)=>{
    // console.log(req.query)
    var ID = utils.generateUUID()
    await db.set(`inLine.${ID}`, {
        prompt: req.query.prompt,
        model: req.query.model,
        status: "wait",
        username: req.query.username ?? "public",
        sample: req.query.sample
    })
    await db.push(`line`, ID)
    const line = await db.get("line")
    res.json({
        status:"QUEUED",
        id: ID,
        position: line.indexOf(ID)+1,
        username: req.query.username
    })
})

app.get("/image/:id", async (req, res)=>{
    if (!req.query.username) res.sendFile(path.join(__dirname, "imgs", "public", req.params.id+".png")); else {
        res.sendFile(path.join(__dirname, "imgs", req.query.username, req.params.id+".png"))
    }
})

app.get("/all/:user", async (req, res)=>{
    const files = fs.readdirSync(`imgs/${req.params.user}`)
    var html = `
    <style>
    .grid-container {
        display: grid;
        grid-template-columns: auto auto auto;
      }
    </style>
    <div class="grid-container">
    `
    
    for (var file of files){
        var rawName = file.replace(".png", "")
        var allData = await db.get(`inLine.${rawName}`)
        html += `<div><center><h1>${allData.prompt}</h1><img src="/image/${rawName}?username=${req.params.user}" style=""></center></div>`
    }

    html += "</div>"
    res.send(html)
})

app.listen(3504, ()=>{
    console.log("Running http://localhost:3504")
})