library(psych)
library(ggplot2)
library(reshape2)
library(betareg)


setwd("/Users/adambreuer/Downloads/political_tv_ads_project/AI-SummarizeVid/VALIDATION")


## ICC calculations ##
##################
dat1<-read.csv('validation_data/ICC_trimtime_RA1_sh.csv',as.is=T)
colnames(dat1)[colnames(dat1) == "Video"] ="video_id"

standardizetime1and3 <-function(x) {
	elements = unlist(strsplit(x,':'))
	secs = as.numeric(elements[1])*3600 + as.numeric(elements[2])*60 + as.numeric(elements[3]) + as.numeric(elements[4])/1000 # note that the 4th element is a fraction
	return(secs)
}

dat1$start_time1<-dat1$Start
dat1$start_time1[dat1$start_time1=="00:00:09::910"]<-"00:00:09:910"
dat1$start_time1<-sapply(dat1$start_time1, standardizetime1and3, USE.NAMES=F)

dat1$stop_time1<-dat1$Stop
dat1$stop_time1[dat1$stop_time1=="0001:16:676"]<-"00:01:16:676"
dat1$stop_time1[dat1$stop_time1=="00:01:11;271"]<-"00:01:11:271"
dat1$stop_time1<-sapply(dat1$stop_time1, standardizetime1and3, USE.NAMES=F)



dat2<-read.csv('validation_data/ICC_trimtime_RA2_de.csv',as.is=T)
colnames(dat2)[colnames(dat2) == "Video.ID"] ="video_id"

standardizetime2 <-function(x) {
	elements = unlist(strsplit(x,';'))
	secs = as.numeric(elements[1])*3600 + as.numeric(elements[2])*60 + as.numeric(elements[3])  
	return(secs)
}

dat2$start_time2<-dat2$Start
dat2$start_time2<-sapply(dat2$start_time2, standardizetime2, USE.NAMES = F)

dat2$stop_time2<-dat2$Stop
dat2$stop_time2[dat2$stop_time2=="00;01;14,100"]<-"00;01;14.100"
dat2$stop_time2[dat2$stop_time2=="00;01.30.500"]<-"00;01;30.500"
dat2$stop_time2<-sapply(dat2$stop_time2, standardizetime2, USE.NAMES = F)



dat3<-read.csv('validation_data/ICC_trimtime_RA3_yu.csv',as.is=T)
colnames(dat3)[colnames(dat3) == "video_iD"] ="video_id"

dat3$start_time3<-dat3$Start
dat3$start_time3[dat3$start_time=="00:0015:200"]<-"00:00:15:200"

dat3$start_time3<-sapply(dat3$start_time3, standardizetime1and3, USE.NAMES=F)
dat3$stop_time3<-dat3$Stop
dat3$stop_time3<-sapply(dat3$stop_time3, standardizetime1and3, USE.NAMES=F)
dat3$stop_time3<-as.numeric(dat3$stop_time3)

dat <- merge(dat1, dat2, by='video_id')
dat <- merge(dat, dat3, by='video_id')

demean_byrow <-function(row) {return( row - sum(row)/length(row) )}

dat_starts <- dat[,c('video_id', 'start_time1', 'start_time2', 'start_time3')]
dat_starts <- na.omit(dat_starts)
# dat_starts_demeaned <- cbind( dat_starts[1], (dat_starts[c(2,3,4)] - rowMeans(dat_starts[c(2,3,4)])) )

dat_stops <- dat[,c('video_id', 'stop_time1', 'stop_time2', 'stop_time3')]
dat_stops <- na.omit(dat_stops)
# dat_stops_demeaned <- cbind( dat_stops[1], (dat_stops[c(2,3,4)] - rowMeans(dat_stops[c(2,3,4)])) )

ICC(dat_starts[,c(2,3,4)],lmer=FALSE)
# ICC(dat_starts_demeaned[,c(2,3,4)], lmer=FALSE)

ICC(dat_stops[,c(2,3,4)],lmer=FALSE)
# ICC(dat_stops_demeaned[,c(2,3,4)], lmer=FALSE)


# Mean absolute difference between raters:
dat_starts_diffs <- dat_starts
dat_starts_diffs$onetwo <- abs(dat_starts_diffs$start_time1 - dat_starts_diffs$start_time2)
dat_starts_diffs$onethree <- abs(dat_starts_diffs$start_time1 - dat_starts_diffs$start_time3)
dat_starts_diffs$twothree <- abs(dat_starts_diffs$start_time2 - dat_starts_diffs$start_time3)
mean_abs_diff_starts <- mean(as.matrix(dat_starts_diffs[,c('onetwo', 'onethree', 'twothree')]))
mean_abs_diff_starts

dat_stops_diffs <- dat_stops
dat_stops_diffs$onetwo = abs(dat_stops_diffs$stop_time1 - dat_stops_diffs$stop_time2)
dat_stops_diffs$onethree = abs(dat_stops_diffs$stop_time1 - dat_stops_diffs$stop_time3)
dat_stops_diffs$twothree = abs(dat_stops_diffs$stop_time2 - dat_stops_diffs$stop_time3)
mean_abs_diff_stops <-mean(as.matrix(dat_stops_diffs[,c('onetwo', 'onethree', 'twothree')]))
mean_abs_diff_stops


## Open and join with actual trimming times and then check against them
META <-read.csv('validation_data/METADATA_trimming.csv') # this file includes the inferred trim times

dat_starts_val = merge(dat_starts, META[,c('ID', 'inferred_start_incl_manuals')], by.x='video_id', by.y='ID')
dat_stops_val = merge(dat_stops, META[,c('ID', 'inferred_end_incl_manuals')], by.x='video_id', by.y='ID')
nrow(dat_starts) == nrow(dat_starts_val) # assert
nrow(dat_stops_val) == nrow(dat_stops_val) # assert

TOLERANCE_SEC_INTERCODER = 1 # seconds 

dat_starts_val$errors_vs_rater2 = dat_starts_val$start_time2 - dat_starts_val$inferred_start_incl_manuals
mean(dat_starts_val$errors_vs_rater2 > TOLERANCE_SEC_INTERCODER) # Our method picks a sooner-than-true start (OK)
mean(dat_starts_val$errors_vs_rater2 < -TOLERANCE_SEC_INTERCODER) #  Our method picks a later-than-true start (less OK)
plot(dat_starts_val$start_time2, dat_starts_val$inferred_start_incl_manuals) 
# This is just the 210 from the inter-coder validation

dat_stops_val$errors_vs_rater2 = dat_stops_val$stop_time2 - dat_stops_val$inferred_end_incl_manuals
mean(dat_stops_val $errors_vs_rater2 > TOLERANCE_SEC_INTERCODER)  # Our method picks a sooner-than-true ending (less OK)
mean(dat_stops_val $errors_vs_rater2 < -TOLERANCE_SEC_INTERCODER) # Our method picks a later-than-true ending (OK)
plot(dat_stops_val$stop_time2, dat_stops_val$inferred_end_incl_manuals)
# This is just the 210 from the inter-coder validation



## Validation results using all ~900 stratified samples 
preproc <- read.csv('validation_data/trim_validation_stratified_rep.csv')

preprocstart <- merge(preproc[,c('COMPONENT_ID', 'PARTY', 'ELECTION_YEAR', 'coded_start')], META[,c('ID', 'inferred_start_incl_manuals')], by.x='COMPONENT_ID', by.y='ID' )
preprocstart$start_errors = preprocstart $coded_start - preprocstart $inferred_start_incl_manuals

trim_start_stratify_plot = ggplot(preprocstart, aes(x= ELECTION_YEAR, y= start_errors,  colour=PARTY)) + geom_point(alpha=0.2, size=0.5)
trim_start_stratify_plot


preprocend <- merge(preproc[,c('COMPONENT_ID', 'PARTY', 'ELECTION_YEAR', 'coded_end')], META[,c('ID', 'inferred_end_incl_manuals')], by.x='COMPONENT_ID', by.y='ID' )
preprocend$end_errors = preprocend $coded_end - preprocend $inferred_end_incl_manuals

trim_end_stratify_plot = ggplot(preprocend, aes(x= ELECTION_YEAR, y= end_errors,  colour=PARTY)) + geom_point(alpha=0.2, size=0.5)
trim_end_stratify_plot

nrow(preproc) == nrow(preprocstart) # assert
nrow(preproc) == nrow(preprocend) # assert

# table(preproc$sample_round)
# plot(preprocstart$coded_start, preprocstart $inferred_start_incl_manuals) 
# plot(preprocend$coded_end, preprocend$inferred_end_incl_manuals)

 
TOLERANCE_SEC_VALIDATION = 3

preprocstart_coded = na.omit(preprocstart)
mean((preprocstart_coded $coded_start - preprocstart_coded $inferred_start_incl_manuals) > TOLERANCE_SEC_VALIDATION) # Our method picks a sooner-than-true start (OK)
mean((preprocstart_coded $coded_start - preprocstart_coded $inferred_start_incl_manuals) < -TOLERANCE_SEC_VALIDATION) #  Our method picks a later-than-true start (less OK)

preprocend_coded = na.omit(preprocend)
mean((preprocend_coded $coded_end - preprocend_coded $inferred_end_incl_manuals) > TOLERANCE_SEC_VALIDATION) # Our method picks a sooner-than-true end (less OK)
mean((preprocend_coded $coded_end - preprocend_coded $inferred_end_incl_manuals) < -TOLERANCE_SEC_VALIDATION) #  Our method picks a later-than-true end (OK)

# In cases where 
err_end =(preprocend_coded $inferred_end_incl_manuals - preprocend_coded $coded_end)
mean(err_end[err_end> TOLERANCE_SEC_VALIDATION])
mean(err_end[err_end>0])


# Check that start error, end error, and |start_err|+|end_err| are uncorrelated with party and year:
preproc_correrrtest <- merge(preproc[,c('COMPONENT_ID', 'PARTY', 'ELECTION_YEAR', 'coded_start', 'coded_end')], META[,c('ID', 'inferred_start_incl_manuals', 'inferred_end_incl_manuals')], by.x='COMPONENT_ID', by.y='ID' )
preproc_correrrtest$starterr = preproc_correrrtest $coded_start - preproc_correrrtest $inferred_start_incl_manuals
preproc_correrrtest$enderr = preproc_correrrtest $coded_end - preproc_correrrtest $inferred_end_incl_manuals


reg_start = lm(data= preproc_correrrtest, starterr ~ PARTY + ELECTION_YEAR + PARTY*ELECTION_YEAR)
reg_end = lm(data= preproc_correrrtest, enderr ~ PARTY + ELECTION_YEAR + PARTY*ELECTION_YEAR)
reg_absstartplusabsend = lm(data= preproc_correrrtest, (abs(starterr)+abs(enderr)) ~ PARTY + ELECTION_YEAR + PARTY*ELECTION_YEAR)


summary(reg_start)
summary(reg_end)
summary(reg_absstartplusabsend)


# Automatically set up the regression table
library(stargazer)
stargazer(
reg_start, reg_end, reg_absstartplusabsend,
title="Beta regression of trimming errors on partisanship and year",
dep.var.labels=c("Error_{start}", "Error_{end}", "|Error_{start}|+|Error_{end}|"),
covariate.labels=c("Republican","Election Year","Repub.*Elec.Year"),
omit.stat=c("LL","ser","f")
)



