package com.saolasoft.websocket.ws;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;
import org.springframework.web.socket.WebSocketSession;

@Getter
@Setter
@AllArgsConstructor
public class IncomingWebSocketSession {

    private String session3dId;

    private WebSocketSession webSocketSession;

}
