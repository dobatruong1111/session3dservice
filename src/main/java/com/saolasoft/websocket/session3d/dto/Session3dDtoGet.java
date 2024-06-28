package com.saolasoft.websocket.session3d.dto;

import com.saolasoft.websocket.session3d.model.Session3d;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
public class Session3dDtoGet {
	
	private String id;

	private String websocketUrl;
}
