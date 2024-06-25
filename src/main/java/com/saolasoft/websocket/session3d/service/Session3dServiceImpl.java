package com.saolasoft.websocket.session3d.service;

import com.saolasoft.websocket.session3d.dto.Session3dDtoCreate;
import com.saolasoft.websocket.session3d.dto.Session3dDtoGet;
import com.saolasoft.websocket.config.AppConfigProperties;
import com.saolasoft.websocket.config.ConfigProperties;
import com.saolasoft.websocket.session3d.model.Session3d;
import com.saolasoft.websocket.session3d.repository.Session3dRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class Session3dServiceImpl implements Session3dService {

    @Autowired
    private Session3dRepository session3DRepository;

    @Autowired
    private ProcessManager processManager;

    @Autowired
    private ResourceManager resourceManager;

    @Autowired
    private ConfigProperties configProperties;

    @Autowired
    private AppConfigProperties appConfigProperties;

    @Override
    public Session3dDtoGet create(Session3dDtoCreate object) {
        // 1. Try to free any available resource
        freeDanglingProcesses();

        // 2. Create new session
        String resource = resourceManager.getNextResource();
        if (resource.isEmpty()) return null;

        String id = UUID.randomUUID().toString();
        String host = resource.split(":")[0];

        int port = Integer.parseInt(resource.split(":")[1]);

        String sessionUrl = String.format(configProperties.getSessionUrl(), id);

        List<String> cmd = appConfigProperties.getViewer().getCmd();
        String replacedCmd = String.format(String.join(" ", cmd), host, port);

        Session3d session = new Session3d(id, host, port, sessionUrl, replacedCmd);

        // 3. Wait until session to be ready
        if (!processManager.startProcess(session)) {
            resourceManager.freeResource(host, port);
            return null;
        }

        // 4. Save session into DB
        session3DRepository.save(session);

        return new Session3dDtoGet(id, sessionUrl);
    }

    // Kill unused/ dangling/ obsolete process
    private void freeDanglingProcesses() {
        List<String> idToFree = processManager.listEndedProcess();
        for (String id: idToFree) {
            session3DRepository.deleteById(id);
            processManager.stopProcess(id);
        }
    }

    @Override
    public Session3dDtoGet getById(String id) {
        return new Session3dDtoGet(session3DRepository.getById(id));
    }

    @Override
    public void terminateSession(String session3dId) {
        // 1. Remove from Database
        session3DRepository.deleteById(session3dId);

        // 2. Free resource and Stop process
    }

    @Override
    public void doFunction(String id, long val, double xya) {

    }
}
