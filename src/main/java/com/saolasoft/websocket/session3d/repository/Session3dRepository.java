package com.saolasoft.websocket.session3d.repository;

import com.saolasoft.websocket.session3d.model.Session3d;
import org.springframework.stereotype.Repository;

import java.util.HashMap;
import java.util.Map;

@Repository
public class Session3dRepository {

    private Map<String, Session3d> sessions = new HashMap<>();

    public Session3d save(Session3d session) {
        sessions.put(session.getId(), session);
        return session;
    }

    public Session3d getById(String sessionId) {
        return sessions.get(sessionId);
    }

    public void deleteById(String id) {
        sessions.remove(id);
    }

    public Map<String, Session3d> getAll() {
        return this.sessions;
    }
}
