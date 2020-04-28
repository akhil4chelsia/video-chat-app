
navigator.mediaDevices.getUserMedia({ video: true, audio: true })
    .then(stream => {

        const video = document.querySelector('video')
        video.srcObject = stream
        video.play()

        client = {}

        var ws = new WebSocket("wss://h6ae1orck3.execute-api.ap-south-1.amazonaws.com/api");

        function CreateVideo(stream) {
            let video = document.createElement('video')
            video.id = 'peerVideo'
            video.srcObject = stream
            video.class = 'embed-responsive-item'
            document.querySelector('#peerDiv').appendChild(video)
            video.play()
        }

        function InitPeer(type) {
            let config = {
                iceServers: [
                    {
                        urls: "stun:numb.viagenie.ca",
                        username: "pasaseh@ether123.net",
                        credential: "12345678"
                    },
                    {
                        urls: "turn:numb.viagenie.ca",
                        username: "pasaseh@ether123.net",
                        credential: "12345678"
                    }
                ]
            }
            let params = {
                initiator: (type == 'init') ? true : false, stream: stream, trickle: false, config: config
            }
            let peer = new SimplePeer(params)
            peer.on('stream', function (stream) {
                console.log('Akhil:Got stream from peer...')
                CreateVideo(stream)
            })
            peer.on('close', function () {
                document.getElementById('peerVideo').remove()
                peer.destroy()
            })

            return peer
        }


        ws.onopen = function () {
            let data = '{"action": "check" } '
            console.log('checking peer count in db')
            ws.send(data);
        }

        ws.onmessage = function (evt) {

            var data = JSON.parse(evt.data)
            console.log('onmessage', data)

            if (data.trigger == 'InitPeer') {
                console.log('Recieved InitPeer trigger.')
                client.gotAnswer = false
                let peer = InitPeer('init')
                peer.on('signal', function (offer) {
                    if (!client.gotAnswer) {
                        let data = '{"action": "offer","Offer": ' + JSON.stringify(offer) + ' } '
                        console.log('sending data', offer)
                        ws.send(data);
                    }
                })

                client.peer = peer
            }

            if (data.Offer) {
                console.log('got offer...', data.Offer)
                let peer = InitPeer('NotInit')
                peer.on('signal', (answer) => {
                    let dataObj = '{"action": "answer","Answer": ' + JSON.stringify(answer) + ' , "ConnectionID": "' + data.ConnectionID + '" } '
                    console.log('sending answer...', dataObj)
                    ws.send(dataObj)
                })
                peer.signal(data.Offer)
            }

            if (data.Answer) {
                console.log('got answer...', data.Answer)
                client.gotAnswer = true
                let peer = client.peer
                peer.signal(data.Answer)
            }

        }

        ws.onclose = function () {
            console.log("Connection is closed");
        };

    })
    .catch(err => {
        document.write(err)
    })