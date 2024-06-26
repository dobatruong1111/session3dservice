package com.saolasoft.websocket.session3d.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
public class Session3dDtoCreate {
	
	private String studyUID;

	private String seriesUID;
}
