package com.saolasoft.websocket.ws;

import com.saolasoft.websocket.ws.WebSocketHandler;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import java.net.URI;
import java.nio.ByteBuffer;

public class WsClient extends WebSocketClient {

    private final String sessionId;
    private final WebSocketHandler handler;

    public WsClient(String sessionId, WebSocketHandler handler, String sessionUrl) throws Exception {
        super(new URI(sessionUrl));
        this.sessionId = sessionId;
        this.handler = handler;
    }

    @Override
    public void onOpen(ServerHandshake handshake) {
        System.out.println("Connected to server: " + sessionId);
    }

    @Override
    public void onMessage(String message) {
    	try {
            handler.sendMessageToClient(sessionId, message);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    @Override
    public void onMessage(ByteBuffer bytes) {
    	try {
            handler.sendBinaryMessageToClient(sessionId, bytes.array());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onClose(int code, String reason, boolean remote) {
        System.out.println("Connection closed: " + sessionId);
    }

    @Override
    public void onError(Exception ex) {
        ex.printStackTrace();
    }

    public void connectToServer(String url) throws Exception {
        super.uri = new URI(url);
        this.connect();
    }

    public void sendMessage(String message) {
        this.send(message);
    }
    
    public void sendMessage(byte[] bytes) {
        this.send(bytes);
    }

    public boolean isConnected() {
        return this.isOpen();
    }
}
