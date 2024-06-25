package com.saolasoft.websocket.session3d.service;

import com.saolasoft.websocket.session3d.dto.Session3dDtoCreate;
import com.saolasoft.websocket.session3d.dto.Session3dDtoGet;

public interface Session3dService {

    Session3dDtoGet create(Session3dDtoCreate object);

    Session3dDtoGet getById(String id);

    void terminateSession(String session3dId);

    void doFunction(String id, long val, double xya);

}
