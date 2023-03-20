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
            model: nextData.model
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
        fs.writeFileSync(`imgs/${req.params.id}.png`, imgb64)
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
        position: line.indexOf(req.params.id)+1
    })
})

app.get("/generate", async (req, res)=>{
    // console.log(req.query)
    var ID = utils.generateUUID()
    await db.set(`inLine.${ID}`, {
        prompt: req.query.prompt,
        model: req.query.model,
        status: "wait"
    })
    await db.push(`line`, ID)
    res.json({
        status:"QUEUED",
        id: ID
    })
})

app.get("/image/:id", async (req, res)=>{
    await db.delete(`inLine.${req.params.id}`)
    res.sendFile(path.join(__dirname, "imgs", req.params.id+".png"))
})

app.listen(3504, ()=>{
    console.log("Running http://localhost:3504")
})