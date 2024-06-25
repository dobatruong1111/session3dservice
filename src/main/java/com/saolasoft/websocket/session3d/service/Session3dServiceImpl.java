package com.saolasoft.websocket.session3d.service;

import com.saolasoft.websocket.session3d.dto.Session3dDtoCreate;
import com.saolasoft.websocket.session3d.dto.Session3dDtoGet;
import com.saolasoft.websocket.config.AppConfigProperties;
import com.saolasoft.websocket.config.ConfigProperties;
import com.saolasoft.websocket.session3d.model.Session3d;
import com.saolasoft.websocket.session3d.repository.Session3dRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.File;
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
        // Try to free any available resource
        freeDanglingProcesses();

        // Create a new session
        String resource = resourceManager.getNextResource();
        if (resource.isEmpty()) return null;

        String id = UUID.randomUUID().toString();
        
        String host = resource.split(":")[0];

        int port = Integer.parseInt(resource.split(":")[1]);

        String sessionUrl = String.format(configProperties.getSessionUrl(), id);

        String cmd = String.format(String.join(" ", appConfigProperties.getViewer().getCmd()), host, port);

        Session3d session = new Session3d(id, host, port, sessionUrl, cmd);

        // Wait until process to be ready
        if (!processManager.startProcess(session)) {
            resourceManager.freeResource(host, port);
            return null;
        }

        // Save session into DB
        session3DRepository.save(session);

        return new Session3dDtoGet(id, sessionUrl);
    }

    // Kill unused/dangling/obsolete process
    private void freeDanglingProcesses() {
        List<String> idToFree = processManager.listEndedProcess();
        for (String id: idToFree) {
        	// Stop process
        	processManager.stopProcess(id);
        	
        	// Delete log file
        	String logFilePath = processManager.getLogFilePath(id);
        	File logFile = new File(logFilePath);
        	logFile.delete();
        	
        	// Get session in DB by id
        	Session3d session = session3DRepository.getById(id);
        	
        	// Free resource
        	resourceManager.freeResource(session.getHost(), session.getPort());
        	
        	// Delete session in DB
            session3DRepository.deleteById(id);
        }
    }

    @Override
    public Session3dDtoGet getById(String id) {
        return new Session3dDtoGet(session3DRepository.getById(id));
    }
}
