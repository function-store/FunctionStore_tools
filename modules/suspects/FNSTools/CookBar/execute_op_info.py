def frameStart(frame):

	active = me.fetch('active')
	
	if active:
		
		targetCOMP = me.fetch('targetCOMP')

		if targetCOMP:


			netX = me.fetch('netX')
			netY = me.fetch('netY')
			netWidth = me.fetch('netWidth')
			netHeight = me.fetch('netHeight')
			netZoom = me.fetch('netZoom')

			tableTitles = ['name', 'x', 'y', 'width', 'height', 'border', 'isCOMP', 'cooking', 'cookTime', 'childrenCooking', 'childrenCookTime', 'gpuMemory', 'childrenGpuMemory']
			tableText = '\t'.join(tableTitles)
			
			tableRowsDistDict = []


			for child in targetCOMP.children:
				
				if not child.expose:
					continue

				if not child.showDocked:
					continue

				name = child.name
				isCOMP = int(child.family == 'COMP')
				isTOP = int(child.family == 'TOP')

				cooking = int(child.cookedThisFrame or child.cookedPreviousFrame)
				cookTime = child.cookTime + child.gpuCookTime
				childrenCooking = int(child.childrenCookAbsFrame >= absTime.frame - absTime.step)
				childrenCookTime = child.childrenCookTime + child.childrenGPUCookTime

				current = child.current
				selected = child.selected
				border = 2
				if current: border = 11
				elif selected: border = 4

				opX = child.nodeX
				opY = child.nodeY
				opWidth = child.nodeWidth
				opHeight = child.nodeHeight
				
				x = (opX - netX) * netZoom + netWidth / 2
				y = (opY - netY) * netZoom + netHeight / 2
				width = opWidth * netZoom
				height = opHeight * netZoom

				edge = me.fetch('barHeight')
				edgeRel = edge * netZoom


				outsideTopBar = False
				cookLevel = cookTime
				if cookLevel < 1: cookLevel = 1
				if cookLevel > 10: cookLevel = 10
				edgeRelLevel = edgeRel * cookLevel
				if x + width + border < 0 or x - border > netWidth or\
				   y + height + border + edgeRelLevel < 0 or y + height + border > netHeight:
					outsideTopBar = True

				outsideBottomBar = True
				if isCOMP:
					outsideBottomBar = False
					childrenCookLevel = childrenCookTime
					if childrenCookLevel < 1: childrenCookLevel = 1
					if childrenCookLevel > 10: childrenCookLevel = 10
					childrenEdgeRelLevel = edgeRel * childrenCookLevel
					if x + width + border < 0 or x - border > netWidth or\
					   y - border < 0 or y - border - childrenEdgeRelLevel > netHeight:
						outsideBottomBar = True

				if outsideTopBar and outsideBottomBar:
					continue

				# FNSTools: GPU memory only for operators in view, and a COMP's
				# total from TD's own childrenGPUMemory() (OP Class). The Python
				# walk this replaces visited every nested operator every frame:
				# 7.5 ms against 0.9 ms over /FNSTools, with identical totals.
				gpuMemory = child.gpuMemory if isTOP else 0
				childrenGpuMemory = child.childrenGPUMemory() if isCOMP else 0

				tableRowVals =[name, x, y, width, height, border, isCOMP, cooking, cookTime, childrenCooking, childrenCookTime, gpuMemory, childrenGpuMemory]
				tableRow = [str(val) for val in tableRowVals]

				opDistX = opX + opWidth / 2 - netX
				opDistY = opY + opHeight / 2 - netY
				opDist = tdu.Vector(opDistX, opDistY, 0).length()
				tableRowDistDict = {
					'tableRow': tableRow,
					'opDist': opDist
				}

				added = False
				for i in range(len(tableRowsDistDict)):
					if tableRowsDistDict[i]['opDist'] > opDist:
						tableRowsDistDict.insert(i, tableRowDistDict)
						added = True
						break
				if not added:
					tableRowsDistDict.append(tableRowDistDict)


			maxOPs = parent().par.Maxops
			tableRowsDistDictCropped = tableRowsDistDict[:maxOPs]
			tableRows = [tableRowDistDict['tableRow'] for tableRowDistDict in tableRowsDistDictCropped]
			tableText += '\n' + '\n'.join(['\t'.join(tableRow) for tableRow in tableRows])
			
			op('table_op_info').clear()
			op('table_op_info').text = tableText
