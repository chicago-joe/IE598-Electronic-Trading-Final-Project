library(xts)
library(quantmod) 
library(PerformanceAnalytics)
library(pracma)
library(fOptions)
library(RND)
library(mnormt)
library(stats4)
library(tseries)
library(fGarch)

setwd("C:/Users/43739/OneDrive/us/2019 spring/paper trading")
BA<-read.csv(file="BA.csv", header=TRUE, sep=",")
rownames(BA)<-BA[,1]
Price<-cbind(BA[,c(6,1)],rep(0,3271))
colnames(Price)<-c("BA","Time","Monthly Avg")

plot(Price[,1],type='l')

for(i in 90:3271){
  temp=0
  for(j in 1:90){
    temp=temp+Price[i+j-60,1]
  }
  Price[i,3]=temp/90
}
Price=Price[90:3271,]
Plotlist=cbind(Price[,c(1,2)],Price[,3]*1.1,Price[3]*0.90)
Plotlist<-Plotlist[,-2]
colnames(Plotlist)<-c("BA","1.1AVG","0.90AVG")

#whole
plot(Plotlist[,1], ylim=c(0,400),type="l")
par(new=TRUE)
plot(Plotlist[,2], ylim=c(0,400),type="l")
par(new=TRUE)
plot(Plotlist[,3], ylim=c(0,400),type="l")

#from 700day to 1000day
plot(Plotlist[700:1000,1], ylim=c(20,80),type="l")
par(new=TRUE)
plot(Plotlist[700:1000,2], ylim=c(20,80),type="l")
par(new=TRUE)
plot(Plotlist[700:1000,3], ylim=c(20,80),type="l")
# buy when price goes down the 0.9 avg and sell when price goes up the 1.1avg
