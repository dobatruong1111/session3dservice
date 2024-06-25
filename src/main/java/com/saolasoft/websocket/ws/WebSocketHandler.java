package com.saolasoft.websocket.ws;

import com.saolasoft.websocket.session3d.dto.Session3dDtoGet;
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
        logger.info("afterConnectionEstablished");

        URI uri = session.getUri();
        String query = uri.getQuery();
        if (query == null) {
            session.close();
            return;
        }

        // Extract session3d id
        String session3dId = query.split("&")[0].split("=")[1];
        // Get session3d by id
        Session3dDtoGet session3d = session3dService.getById(session3dId);
        //logger.info(String.format("Session3d: id=%s, host=%s, port=%d, cmd=%s", session3d.getId(), session3d.getHost(), session3d.getPort(), session3d.getCmd()));

        incomingWsSessions.put(session.getId(), new IncomingWebSocketSession(session3dId, session));
        // Optionally, connect to other WebSocket servers
        String sessionUrl = String.format("ws://%s:%d/ws", session3d.getHost(), session3d.getPort());
        WsClient client = new WsClient(session.getId(), this, sessionUrl);
        client.connectToServer(sessionUrl);
        outgoingWsClients.put(session.getId(), client);
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        logger.info("handleTextMessage - message: " + message.getPayload());

        // Forward message to another WebSocket server
        WsClient client = outgoingWsClients.get(session.getId());
        if (client != null && client.isConnected()) {
            client.sendMessage(message.getPayload());
        }
    }

    @Override
    protected void handleBinaryMessage(WebSocketSession session, BinaryMessage message) throws Exception {
        logger.info("handleBinaryMessage : " + message.toString());

        // Forward binary message to another WebSocket server
        WsClient client = outgoingWsClients.get(session.getId());
        if (client != null && client.isConnected()) {
            client.sendMessage(message.getPayload().array());
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        logger.info("afterConnectionClosed");

        IncomingWebSocketSession webSocketSession = incomingWsSessions.remove(session.getId());
        WsClient client = outgoingWsClients.remove(session.getId());
        if (client != null) {
            client.close();
        }

        // Remove 3D session
        session3dService.terminateSession(webSocketSession.getSession3dId());
    }

    public void sendMessageToClient(String sessionId, String message) throws Exception {
        logger.info("sendMessageToClient");

        WebSocketSession session = incomingWsSessions.get(sessionId).getWebSocketSession();
        if (session != null && session.isOpen()) {
            session.sendMessage(new TextMessage(message));
        }
    }

    public void sendBinaryMessageToClient(String sessionId, byte[] message) throws Exception {
        logger.info("sendBinaryMessageToClient");

        WebSocketSession session = incomingWsSessions.get(sessionId).getWebSocketSession();
        if (session != null && session.isOpen()) {
            session.sendMessage(new BinaryMessage(message));
        }
    }

}
