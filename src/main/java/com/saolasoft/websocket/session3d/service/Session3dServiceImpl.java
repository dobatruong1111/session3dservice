package com.saolasoft.websocket.session3d.service;

import com.saolasoft.websocket.session3d.dto.Session3dDtoCreate;
import com.saolasoft.websocket.session3d.dto.Session3dDtoGet;
import com.saolasoft.websocket.config.AppConfigProperties;
import com.saolasoft.websocket.config.ConfigProperties;
import com.saolasoft.websocket.session3d.model.Session3d;
import com.saolasoft.websocket.session3d.repository.Session3dRepository;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.File;
import java.util.*;

@Service
public class Session3dServiceImpl implements Session3dService {

    private final Logger logger = LoggerFactory.getLogger(getClass());

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

        String cmd = String.format(String.join(" ", appConfigProperties.getViewer().getCmd()), host, port, object.getStudyUID(), object.getSeriesUID(), object.getSession2D());

        Session3d session3d = new Session3d(id, host, port, sessionUrl, cmd);
        // logger.info(String.format("Session3d: id=%s, host=%s, port=%d", session3d.getId(), session3d.getHost(), session3d.getPort()));

        // Wait until process to be ready
        if (!processManager.startProcess(session3d)) {
            resourceManager.freeResource(host, port);
            return null;
        }

        // Save session into DB
        session3DRepository.save(session3d);

        return new Session3dDtoGet(id, sessionUrl);
    }

    // Kill unused/dangling/obsolete process
    private void freeDanglingProcesses() {
        List<String> idToFree = processManager.listEndedProcess();
        for (String id: idToFree) {
        	deleteById(id);
        }
    }

    @Override
    public Session3d getById(String id) {
        return session3DRepository.getById(id);
    }

    @Override
    public void deleteById(String id) {
        // Stop process
        processManager.stopProcess(id);

        // Delete log file
        String logFilePath = processManager.getLogFilePath(id);
        File logFile = new File(logFilePath);
        if (logFile.exists()) {
            if (!logFile.delete()) {
                logger.info(String.format("Delete %s failed", logFilePath));
            }
        }

        Session3d session3d = session3DRepository.getById(id);
        if (session3d != null) {
            // Free resource
            resourceManager.freeResource(session3d.getHost(), session3d.getPort());

            // Delete session in DB
            session3DRepository.deleteById(id);
        }
    }

    @PreDestroy
    public void onDestroy() {
        Map<String, Session3d> sessions = session3DRepository.getAll();
        for (String id : sessions.keySet()) {
            logger.info(String.format("Stop process with session3d id: %s", id));

            // Stop process
            processManager.stopProcess(id);

            // Delete log file
            String logFilePath = processManager.getLogFilePath(id);
            File logFile = new File(logFilePath);
            if (logFile.exists()) {
                if (!logFile.delete()) {
                    logger.info(String.format("Delete %s failed", logFilePath));
                }
            }
        }
    }
}
