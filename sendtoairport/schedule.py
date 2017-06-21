# coding:utf-8

"""
Donghui Chen, Wangmeng Song
May 15, 2017
修改
Wangmeng Song
june 17,2017
"""
import json
import numpy as np
import copy

import knapsack
import auxfn
import mapAPI

AMAPAIRPORTCOORDINATE = [30.574590, 103.955020]
MAXSEATNUM5 = 5
MAXSEATNUM6 = 6


class DIST:

    # 初步处理数据，传入json字符串resdict,订单人数=5/6的存入getonthecar,getonthecarloc,getonthecarseatnum
    def getAllRepeatData(self, repeatpoid, repeatloc, repeatseatnum, getonthecar, getonthecarloc, getonthecarseatnum, resdict):
        for element in resdict:
            tmp = []
            bdLat = element['bdlat']
            bdLng = element['bdlng']
            loc = auxfn.BD2AMap(bdLat, bdLng)
            gglat = round(loc.lat, 6)
            gglng = round(loc.lng, 6)
            poid = element['BID']
            seatnum = element['seatnum']
            tmp.append(gglat)
            tmp.append(gglng)
            if seatnum is 6 or seatnum is 5:
                getonthecar.append([poid])
                getonthecarloc.append(tuple(tmp))
                getonthecarseatnum.append([seatnum])
            else:
                repeatpoid.append(poid)
                repeatseatnum.append(seatnum)
                repeatloc.append(tuple(tmp))

    # 第二次处理数据，将同一地点的订单集中在一起，duplicateLoc=[[(lat,lng),(lat,lng)]],duplicateorderid=[[ordea,orderb],[orderc]]
    def getDuplicateData(self, repeatOrderID, repeatloc, repeatSeatnum, duplicateOrderid, duplicateSeatNum):
        duplicateLoc = list(set(repeatloc))
        for element in duplicateLoc:
            repeat = auxfn.getAllIndices(element, repeatloc)
            orderidtmp = []
            seatnumtmp = []
            for element1 in repeat:
                orderidtmp.append(repeatOrderID[element1])
                seatnumtmp.append(repeatSeatnum[element1])
            duplicateOrderid.append(orderidtmp)
            duplicateSeatNum.append(seatnumtmp)
        return duplicateLoc

    # 第三次处理数据排除一个地点中=5/6的情况，如果这个地点人数大于6，那么将订单人数相加=5/6存入getonthecar，剩下的订单存入RMMTSID，RMMTSLoc
    def removeMoreThanSixPassenger(self, ID, Loc, Seatnum, RMMTSID, RMMTSLoc, RMMTSseatnum, getontcar, getonthecaloc, getonthecarseatnum):
        for i in range(len(Seatnum)):
            if sum(Seatnum[i]) is MAXSEATNUM6 or sum(Seatnum[i]) is MAXSEATNUM5:
                getontcar.append(ID[i])
                getonthecaloc.append(Loc[i])
                getonthecarseatnum.append(Seatnum[i])
            elif sum(Seatnum[i]) > MAXSEATNUM6:
                tmpSeatnum = copy.copy(Seatnum[i])
                tmpID = copy.copy(ID[i])
                knapsack6 = knapsack.zeroOneKnapsack(tmpSeatnum, MAXSEATNUM6)
                knapsack5 = knapsack.zeroOneKnapsack(tmpSeatnum, MAXSEATNUM5)
                while knapsack6[0] is MAXSEATNUM6 or knapsack5[0] is MAXSEATNUM5:
                    if knapsack6[0] is 6:
                        knapsackvalue = knapsack6[1]
                    else:
                        knapsackvalue = knapsack5[1]
                    tmpalreadygetonthcarid = []
                    storeindex = [j for j, x in enumerate(knapsackvalue) if x is 1]      # 列表推导式
                    for element1 in storeindex:
                        tmpalreadygetonthcarid.append(tmpID[element1])
                    getontcar.append(tmpalreadygetonthcarid)
                    getonthecaloc.append(Loc[i])
                    getonthecarseatnum.append(Seatnum[i])
                    for element2 in reversed(storeindex):
                        del (tmpSeatnum[element2])
                        del (tmpID[element2])
                    if len(tmpSeatnum) > 1:
                        knapsack6 = knapsack.zeroOneKnapsack(tmpSeatnum, MAXSEATNUM6)
                        knapsack5 = knapsack.zeroOneKnapsack(tmpSeatnum, MAXSEATNUM5)
                    elif len(tmpSeatnum) is 1:
                        RMMTSID.append(tmpID)
                        RMMTSLoc.append(Loc[i])
                        RMMTSseatnum.append(tmpSeatnum)
                        break
                    else:
                        break
                else:
                    if sum(tmpSeatnum) < 6:
                        RMMTSID.append(tmpID)
                        RMMTSLoc.append(Loc[i])
                        RMMTSseatnum.append(tmpSeatnum)
                    else:                                       # 增加同一个地点大于6个人订单情况
                        tmpLoc = list(Loc[i])
                        r = 0
                        for k in xrange(len(tmpID)):
                            tmpLoc[0] += r
                            tmpLoc[1] += r
                            RMMTSID.append([tmpID[k]])
                            RMMTSLoc.append(tuple(tmpLoc))
                            RMMTSseatnum.append([tmpSeatnum[k]])
                            r += 0.00001
            else:
                RMMTSID.append(ID[i])
                RMMTSLoc.append(Loc[i])
                RMMTSseatnum.append(Seatnum[i])

    # 如果已经上车的且订单中人数=5，那么寻找它1000米范围内的一个人，如果有就上车且在RMMSID、RMMSLoc、RMMTSseatnum中删除订单信息，如果没有就什么不做
    def getTheFivePersonAroundOnlyOne(self, getonthecar, getonthecarloc, getonthecarseatnum, RMMTSID, RMMTSLoc, RMMTSseatnum):
        tmpRMMTSLoc = copy.copy(RMMTSLoc)
        tmpRMMTSLocVec = self.getOrderLocVec(tmpRMMTSLoc)
        frelement = []
        for i in range(len(getonthecarseatnum)):
            if sum(getonthecarseatnum[i]) is MAXSEATNUM5:   # 修改==为is提高效率
                arounddistvec = auxfn.calcDistVec(getonthecarloc[i], tmpRMMTSLocVec)
                tmpix = np.where(arounddistvec < 1001)
                if len(tmpix[0]) is not 0:
                    ix = [x for x in tmpix[0] if x not in frelement]
                    if len(ix) is not 0:
                        for element in ix:
                            if len(RMMTSseatnum[element]) is 1 and RMMTSseatnum[element][0] is 1:
                                frelement.append(element)
                                getonthecar[i].append(RMMTSID[element][0])
                            else:
                                continue
                    else:
                        continue
                else:
                    continue
            else:
                continue
        if len(frelement) is not 0:
            frelement.sort()
            for element2 in reversed(frelement):
                RMMTSID.pop(element2)
                RMMTSLoc.pop(element2)
                RMMTSseatnum.pop(element2)

    # 检查乘客在车上呆的时间是否满足小于最大时间
    def checkTimeLimitCondition(self, maxTimeLimit, currentPoint, nextPoint, airport, currentScheduleVec):
        GTI = mapAPI.AMapAPI()
        deltaT = GTI.getTimeDistVec(nextPoint, currentPoint, 1)
        nextPoint2airportTime = GTI.getTimeDistVec(airport, nextPoint, 1)
        if np.sum(currentScheduleVec) + deltaT + nextPoint2airportTime - currentScheduleVec[0] <= maxTimeLimit:
            currentScheduleVec.append(deltaT[0])
            currentScheduleVec[0] = nextPoint2airportTime[0]
            return True
        else:
            return False

    # 将orderLocList=[(lat1,lng1),(lat2,lng2)]，转换为2-Darray orderLocVec = [[lat1 lng],[lat2 lng2]]
    def getOrderLocVec(self, orderLocList):
        orderLocVec = np.zeros([len(orderLocList), 2], dtype=float)
        for i in range(len(orderLocList)):
            orderLocVec[i][0] = orderLocList[i][0]
            orderLocVec[i][1] = orderLocList[i][1]
        return orderLocVec

    # 将一个地点的人数orderSeatNumList = [[2],[1,1,1],[2,2]]求和转化为1维数组，orderNum = [2 3 4]
    def getOrderNumVec(self, orderSeatNumList):
        orderNum = np.zeros([len(orderSeatNumList)], dtype='uint')
        for i in range(len(orderSeatNumList)):
            orderNum[i] = sum(orderSeatNumList[i])
        return orderNum

    # 获取一辆车的乘客数据格式为[[2,4,1],[5,6,7]]
    def getCarPassengerList(self, timeList, passengerList):
        numList = []
        for element in timeList:
            numList.append(len(element))
        newNumList = []
        for i in xrange(len(numList) + 1):
            newNumList.append(sum(numList[0:i]))
        carList = []
        for j in xrange(1, len(newNumList)):
            tem = []
            for k in xrange(newNumList[j - 1], newNumList[j]):
                tem.append(passengerList[k])
            carList.append(tem)
        return carList

    # 将一辆车的地点替换为订单[[[A,B],[C],[D]],[[E],[F],[G]]]
    def getThePassengerOrderForEachCar(self, carList, orderID):
        carOrderList = []
        for i in xrange(len(carList)):
            car = []
            for element in carList[i]:
                car.append(orderID[element])
            carOrderList.append(car)
        return carOrderList

    # 将时间添加到订单单信息中[[[A,1800],[B,1800],[C,500],[D,100]],[[E,2000],[F,1000],[G,500]]]
    def getOrderAndTimeInfos(self, carOrderList, OrderTime):
        ret = []
        for m in xrange(len(OrderTime)):
            ret.append([])
            for n in xrange(len(OrderTime[m])):
                sum0 = sum(OrderTime[m])
                sum0 -= sum(OrderTime[m][1:n + 1])
                val = carOrderList[m][n]
                for element in val:
                    tmp = []
                    tmp.append(element)
                    tmp.append(sum0)
                    ret[m].append(tmp)
        return ret


# 获得已经上车的乘客的时间距离getonthecarloc=[(lat1,lng1),(lat2,lng2)],getonthecarorderid=[[A,B,C],[D,E]]
    def gethasgotonthecartimedistance(self, getonthecarloc, getonthecarorderid):
        GTI = mapAPI.AMapAPI()
        if len(getonthecarloc) is not 1:
            orderVec = self.getOrderLocVec(getonthecarloc)
            orderNum = len(orderVec)
        else:
            orderVec = np.array([getonthecarloc[0][0], getonthecarloc[0][1]])
            orderNum = len(getonthecarloc)
        timedistancevec = GTI.getTimeDistVec(AMAPAIRPORTCOORDINATE, orderVec,orderNum)
        hasgetonthecarorderandtime = []    # [[[a,878],[b,788],[c,898]],[[d,658],[e,345]]]
        for i in range(orderNum):
            car = []
            for j in range(len(getonthecarorderid[i])):
                tmp = []
                tmp.append(getonthecarorderid[i][j])
                tmp.append(timedistancevec[i])
                car.append(tmp)
            hasgetonthecarorderandtime.append(car)
        return hasgetonthecarorderandtime
