package com.saolasoft.websocket.session3d.service;

import com.saolasoft.websocket.session3d.dto.Session3dDtoCreate;
import com.saolasoft.websocket.session3d.dto.Session3dDtoGet;
import com.saolasoft.websocket.session3d.model.Session3d;

public interface Session3dService {

    Session3dDtoGet create(Session3dDtoCreate object);

    Session3d getById(String id);

    void deleteById(String id);
}
