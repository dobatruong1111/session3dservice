package com.saolasoft.websocket.session3d.dto;

import com.saolasoft.websocket.session3d.model.Session3d;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class Session3dDtoGet {
	
	private String id;

	private String sessionUrl;
	
	public Session3dDtoGet(String id, String sessionUrl) {
		this.id = id;
		this.sessionUrl = sessionUrl;
	}
}
