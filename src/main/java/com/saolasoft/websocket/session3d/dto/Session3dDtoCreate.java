package com.saolasoft.websocket.session3d.dto;

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
	
	public String getApplication() {
		return this.application;
	}
	
	public String getStudyUID() {
		return this.studyUID;
	}
	
	public String getSeriesUID() {
		return this.seriesUID;
	}
	
	public String getSessionId() {
		return this.sessionId;
	}
}
