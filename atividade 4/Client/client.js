const axios = require('axios')
const express = require("express");
const bodyParser = require("body-parser");
const client = express();
const router = express.Router();
const EventSource = require("eventsource");

const endpoint = 'http://127.0.0.1:5000';
let stream = null;
let username = null;

client.use(bodyParser.urlencoded({ extended: false }));
client.use(bodyParser.json())

router.get('/', async (req, res, next) => {
    const serverRes = await axios.get(endpoint);
    res.send({client: 'online', server: serverRes.data});
})
router.post('/users/new', async (req, res, next) => {
    username = req.body.name;
    const body = {name:username};
    const serverRes = await axios.post(endpoint + '/users/new', body);

    if (serverRes.data.status){
        stream = new EventSource('http://localhost:5000/stream');
        const handler = function (event) {
            const type = event.type;
            if (type !== 'error') {
                console.log(`${type}: ${event.data}`);
            }

            if (type === 'result') {
                stream.close();
                stream = null;
            }
        };
        stream.addEventListener('created', handler);
        stream.addEventListener(username, handler);
        console.log(username);
    }

    res.send(serverRes.data);
})
router.get('/users/list', async (req, res, next) => {
    const serverRes = await axios.get(endpoint + '/users/list');
    res.send(serverRes.data);
})
router.post('/auctions/new', async (req, res, next) => {
    const body = {...req.body,creator:username};
    const serverRes = await axios.post(endpoint + '/auctions/new', body);
    res.send(serverRes.data);
})
router.get('/auctions/list', async (req, res, next) => {
    const serverRes = await axios.get(endpoint + '/auctions/list');
    res.send(serverRes.data);
})
router.get('/auctions/list/active', async (req, res, next) => {
    const serverRes = await axios.get(endpoint + '/auctions/list/active');
    res.send(serverRes.data);
})
router.post('/auctions/bid', async (req, res, next) => {
    const body = {...req.body,ownerBid:username};
    const serverRes = await axios.post(endpoint + '/auctions/bid', body);
    res.send(serverRes.data);
})

client.use(router);


console.log(process.argv[2]);
client.set("port", process.argv[2] || 3000);
client.listen(client.get("port"), function(){
    console.log("Server started on port " + client.get("port"))
});


