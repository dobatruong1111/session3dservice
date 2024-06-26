package com.saolasoft.websocket.session3d.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class Session3dDtoCreate {
	
	private String application;

	private String studyUID;

	private String seriesUID;

	private String sessionId;
	
	public Session3dDtoCreate(String application, String studyUID, String seriesUID, String sessionId) {
		this.application = application;
		this.studyUID = studyUID;
		this.seriesUID = seriesUID;
		this.sessionId = sessionId;
	}
}
