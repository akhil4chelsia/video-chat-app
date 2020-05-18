
navigator.mediaDevices.getUserMedia({ video: true, audio: true })
    .then(stream => {

        const video = document.querySelector('video')
        video.srcObject = stream
        video.play()
        video.muted = "muted";

        function signal(action, inputData = {}) {

            let sessionId = ""
            if(metapeer.session_id){
                sessionId = metapeer.session_id
            }

            let data = '{"action": "signal", "SessionId": "' + sessionId + '" , "Step": "' + action + '" , "Data" : ' + JSON.stringify(inputData) + ' } '
            console.log('signaling : ', JSON.stringify(data))
            ws.send(data);
        }

        var ws = new WebSocket("wss://h6ae1orck3.execute-api.ap-south-1.amazonaws.com/api");

        let peer
        var count = 0
        var client = {}

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


        function gotRemoteStream(stream) {
            console.log('gotRemoteStream')
            const remoteVideo = document.getElementById('peerVideo');
            if (!remoteVideo) {
                let video = document.createElement('video')
                video.id = 'peerVideo'
                video.srcObject = stream
                video.class = 'embed-responsive-item'
                document.querySelector('#peerDiv').appendChild(video)
                video.play()
            }
        }

        function getConfig(type) {
            let initiator = type == 'InitPeer' ? true : false
            return {
                initiator: initiator, stream: stream, trickle: false, config: config, reconnectTimer: 100,
                iceTransportPolicy: 'relay', trickle: true
            }
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
                if(peerVideo){
                    peerVideo.remove();
                }
                signal('WhoAmI')
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

                peer = new SimplePeer(configuration)
                peer.on('stream', function (stream) {
                    gotRemoteStream(stream)
                })
                peer.on('close', function () {
                    console.log('PEER DESTROYED!')
                    let peerVideo = document.getElementById('peerVideo')
                    if(peerVideo){
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


            }

            if (data.IceCandidate) {
                console.log('Recieved Ice Candidate.', data.IceCandidate)
                peer.signal(data.IceCandidate)
            }

            if (data.Offer) {
                console.log('Recieved Offer.', data.Offer)
                peer.signal(data.Offer)
            }

            if (data.Answer) {
                console.log('Recieved Answer.', data.Answer)
                client.gotAnswer = true
                peer.signal(data.Answer)
            }

        }

        ws.onclose = function () {
            console.log('WEBSOCKET CLOSED!')
            peer = null
        };

    })
    .catch(err => {
        document.write(err)
    })