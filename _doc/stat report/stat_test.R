library(xts)
library(quantmod) 
library(PerformanceAnalytics)
library(pracma)
library(fOptions)
library(RND)
library(mnormt)
library(astsa)

setwd("C:/Users/43739/OneDrive/us/2019 spring/paper trading/data")
BPdata<-read.csv(file="intra_bp_2018_1min.csv", header=TRUE, sep=",")
RDSAdata<-read.csv(file="intra_rds-a_2018_1min.csv", header=TRUE, sep=",")
data<-cbind(BPdata,RDSAdata[,-1])
closelist<-data[,c(1,5,9)]
colnames(closelist)<-c("date","BP_close","RDSA_close")

cor(closelist[2],closelist[3])
#0.8544067
#BP=m*RSDA+b
lm_BP_RDSA<-lm(closelist$BP_close~closelist$RDSA_close)
summary(lm_BP_RDSA)
#Intercept
#5.597244
lm_BP_RDSA$coefficients[1]

#Slope
#0.5644122
lm_BP_RDSA$coefficients[2]

res<-closelist$BP_close-(lm_BP_RDSA$coefficients[2]*closelist$RDSA_close+lm_BP_RDSA$coefficients[1])

sd(res)
#1.355027

mean(res)
#7.581291e-13

#AR1
ar1<-sarima(res,1,0,0)

#Hist
hist(res,breaks=100,freq = FALSE,main="Histogram of residuals")
lines(density(res),col="red")
xseq<-seq(-3*sd(res)+mean(res),3*sd(res)+mean(res),.01)
densities<-dnorm(xseq, 0,1)
lines(xseq, densities,col="blue")


plot(res,type='l',main="residuals")

