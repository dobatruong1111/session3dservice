package com.saolasoft.websocket.ws;

import com.saolasoft.websocket.session3d.model.Session3d;
import com.saolasoft.websocket.session3d.service.Session3dService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.*;
import org.springframework.web.socket.handler.AbstractWebSocketHandler;
import java.net.URI;
import java.util.HashMap;
import java.util.Map;

// Create a WebSocket handler to manage incoming connections and forward messages.
@Component
public class WebSocketHandler extends AbstractWebSocketHandler {

    private final Map<String, IncomingWebSocketSession> incomingWsSessions = new HashMap<>();

    private final Map<String, WsClient> outgoingWsClients = new HashMap<>();

    private final Logger logger = LoggerFactory.getLogger(getClass());

    @Autowired
    private Session3dService session3dService;

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        URI uri = session.getUri();
        if (uri != null) {
            String query = uri.getQuery();
            if (query == null) {
                session.close();
                return;
            }

            // Extract id
            String id = query.split("&")[0].split("=")[1];

            // Get session by id
            Session3d session3d = session3dService.getById(id);
            if (session3d == null) {
                session.close();
                return;
            }
            logger.info(String.format("Session3d: id=%s, host=%s, port=%d", session3d.getId(), session3d.getHost(), session3d.getPort()));

            incomingWsSessions.put(session.getId(), new IncomingWebSocketSession(id, session));
            String sessionUrl = String.format("ws://%s:%d/ws", session3d.getHost(), session3d.getPort());
            WsClient client = new WsClient(session.getId(), this, sessionUrl);
            // Connect to server 3d
            client.connectToServer();
            // Save connection
            outgoingWsClients.put(session.getId(), client);
        } else {
            session.close();
        }
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        // Forward message to server 3d
        WsClient client = outgoingWsClients.get(session.getId());
        if (client != null && client.isConnected()) {
            client.sendMessage(message.getPayload());
        }
    }

    @Override
    protected void handleBinaryMessage(WebSocketSession session, BinaryMessage message) throws Exception {
        // Forward binary message to server 3d
        WsClient client = outgoingWsClients.get(session.getId());
        if (client != null && client.isConnected()) {
            client.sendMessage(message.getPayload().array());
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        // After connection closed
        IncomingWebSocketSession webSocketSession = incomingWsSessions.remove(session.getId());
        WsClient client = outgoingWsClients.remove(session.getId());
        if (client != null) {
            client.close();
        }
    }

    public void sendMessageToClient(String sessionId, String message) throws Exception {
        // Send message to client
        WebSocketSession session = incomingWsSessions.get(sessionId).getWebSocketSession();
        if (session != null && session.isOpen()) {
            session.sendMessage(new TextMessage(message));
        }
    }

    public void sendBinaryMessageToClient(String sessionId, byte[] message) throws Exception {
        // Send binary message to client
        WebSocketSession session = incomingWsSessions.get(sessionId).getWebSocketSession();
        if (session != null && session.isOpen()) {
            session.sendMessage(new BinaryMessage(message));
        }
    }
}
