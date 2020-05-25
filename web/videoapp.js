var ws = null
let peers = []

function nextButton() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close()
        init()
        if (peer) {
            peer.destroy()
        }
    }

}


navigator.mediaDevices.getUserMedia({ video: true, audio: true })
    .then(stream => {


        function nextButton2() {
        }

        const video = document.querySelector('video')
        video.srcObject = stream
        video.play()
        video.muted = "muted";

        ws = new WebSocket("wss://nqlfvsvv4e.execute-api.ap-south-1.amazonaws.com/api");

        function signal(action, inputData = {}) {

            let sessionId = ""
            if (metapeer.session_id) {
                sessionId = metapeer.session_id
            }

            let data = '{"action": "signal", "SessionId": "' + sessionId + '" , "Step": "' + action + '" , "Data" : ' + JSON.stringify(inputData) + ' } '
            console.log('signaling : ', JSON.stringify(data))
            ws.send(data);
        }

        function triggerCount() {

            let sessionId = ""
            if (metapeer.session_id) {
                sessionId = metapeer.session_id
            }

            let data = '{"action": "count"}'
            console.log('getting count : ', JSON.stringify(data))
            ws.send(data);
        }

        var count = 0
        var client = {}
        let interval = null

        metapeer = {

        }

        let config = {
            'iceServers': [
                {
                    'urls': 'stun:stun.l.google.com:19302'
                },
                {
                    'urls': 'turn:numb.viagenie.ca?transport=udp',
                    'credential': '3TptDG7cAfz5TaXsda',
                    'username': 'dollysam369@gmail.com'
                }
            ]
        }

        var connectionCount = 0

        function gotRemoteStream(stream) {
            console.log('gotRemoteStream')
            const remoteVideo = document.getElementById('peerVideo' + connectionCount);
            if (!remoteVideo) {
                let video = document.createElement('video')
                video.id = 'peerVideo'
                video.srcObject = stream
                video.class = 'embed-responsive-item'
                document.getElementById('peerDiv' + connectionCount).appendChild(video)
                video.play()
                connectionCount = connectionCount + 1
            }
        }

        function getConfig(type) {
            let initiator = type == 'InitPeer' ? true : false
            return {
                initiator: initiator, stream: stream, trickle: false, config: config, reconnectTimer: 100,
                iceTransportPolicy: 'relay', trickle: true
            }
        }

        function updateOnlineUsers(count) {
            console.log('usersCount:', count)
            document.getElementById('usersCount').innerHTML = count
        }


        ws.onopen = function () {
            signal('WhoAmI')
        }

        ws.onmessage = async function (evt) {

            var data = JSON.parse(evt.data)
            console.log('onmessage', data)

            if (data.PeerDisconnected) {
                peer = null
                let peerVideo = document.getElementById('peerVideo')

                if (peerVideo) {
                    peerVideo.remove();
                }
                signal('WhoAmI')
            }

            if (data.SessionsCount) {
                updateOnlineUsers(data.SessionsCount)
            }

            if (data.WhoAmI) {
                //triggerCount()
                //interval = setInterval(triggerCount, 4000);
            }

            if (data.WhoAmI && "InitPeer" == data.WhoAmI) {
                console.log('Im init peer session:', data.SessionId)
                metapeer.type = data.WhoAmI
                metapeer.session_id = data.SessionId
            }

            if (data.WhoAmI && "NonInitPeer" == data.WhoAmI) {
                console.log('Im non init peer session:', data.SessionId)
                metapeer.type = data.WhoAmI
                metapeer.session_id = data.SessionId
                signal("PeerConnected")
                return
            }

            if (data.PeerStatus && "Connected" == data.PeerStatus) {
                console.log('Your buddy connected. [id] ', data.PeerConnectionId) // Exchange candidate and offer
                metapeer.MyPeerId = data.PeerConnectionId

                let configuration = getConfig(metapeer.type)
                console.log('Configuration:', configuration)

                let peer = new SimplePeer(configuration)
                peer.on('stream', function (stream) {
                    gotRemoteStream(stream)
                })
                peer.on('close', function () {
                    console.log('PEER DESTROYED!')
                    let peerVideo = document.getElementById('peerVideo')

                    if (peerVideo) {
                        peerVideo.remove()
                    }
                    //peer.destroy()
                })

                peer.on('signal', function (entity) {

                    if (entity.type == "offer") {
                        console.log('Sending offer.', entity)
                        signal('Offer', entity)
                    }
                    else if (entity.candidate) {
                        console.log('Sending candidate.', entity)
                        signal('IceCandidate', entity)
                    }
                    else if (entity.type == "answer") {
                        console.log('Sending answer.', entity)
                        signal('Answer', entity)
                    }
                })

                peers.push(peer)

            }

            if (data.IceCandidate) {
                console.log('Recieved Ice Candidate.', data.IceCandidate)
                peers.forEach(peer => {
                    peer.signal(data.IceCandidate)
                })

            }

            if (data.Offer) {
                console.log('Recieved Offer.', data.Offer)
                peers.forEach(peer => {
                    peer.signal(data.Offer)
                })

            }

            if (data.Answer) {
                console.log('Recieved Answer.', data.Answer)
                client.gotAnswer = true
                peers.forEach(peer => {
                    peer.signal(data.Answer)
                })

            }

        }

        ws.onclose = function () {
            console.log('WEBSOCKET CLOSED!')
            //peer = null
            clearInterval(interval)
        };

    })
    .catch(err => {
        document.write(err)
    })

