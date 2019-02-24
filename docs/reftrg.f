      program reftrg
c
c     routine to apply the reftek trigger algorithm
c     to a designated SAC file
c     LTA is initialized to STA after 2 STA time constants
c     Trigger detection begins after trgdly seconds
c
c     compile with: f77 reftrg.f $SACDIR/lib/sac.a -f68881
c
c     Written by T.J. Owens, August 16, 1988
c
      character*32 file
      real lta,sta,ratio,xmean
c
c    Dimension huge arrays for application to long time windows
c
      real x(120000),trig(120000)
      real ysta(120000),ylta(120000)
      real rat(120000)
c
c    get input info
c
      write(6,100) 
  100 format('Enter SAC file: ',$)
      read(5,*) file

      write(6,102)
  102 format('Enter duration for STA (in secs): ',$)
      read(5,*) sta

      write(6,101)
  101 format('Enter duration for LTA (in secs): ',$)
      read(5,*) lta

      write(6,103)
  103 format('Enter STA/LTA ratio: ',$)
      read(5,*) ratio

      write(6,104)
  104 format('LTA will be initialized to STA after 2 STA times',
     *       /,'Enter time delay (in seconds from begining of',
     *         ' trace)',/,'before start of trigger detection: ',$)
      read(5,*) trgdly

      do 900 i=1,10000
  900 x(i) = 0.0
c
c    get the trace data
c
      call rsac1(file,x,npts,beg,dt,120000,nerr)
c
c   establish number of points in LTA and STA windows
c    as well as in trgdly
c
      nlta=int(lta/dt) + 1
      nsta=int(sta/dt) + 1
      ntdly=int(trgdly/dt) + 1
c
c  n100 is number of data points in 100 second window
c      (needed for data mean calculation)
c
      n100=int(100./dt) + 1
c
c     clta and csta are constants in trigger algoritms
c
      clta=1./real(nlta)
      csta=1./real(nsta)

      xmean=0.0
c
c    start the triggering process
c
      do 3 i=1,npts
         nmean=i
         xmean=xmean +x(i)
c
c    after 100 seconds, data mean is mean of previous 100 seconds only
c
         if(i.ge.n100) then
                xmean=xmean - x(i-n100)
                nmean=n100
         endif
c
c    LTA value calculated as per REFTEK algorithm
c
         ylta(i)= clta*abs(x(i) - xmean/real(nmean))
     *          + (1-clta)*ylta(i-1)
c
c    STA value calculated as per REFTEK algorithm
c
         ysta(i)= csta*abs(x(i) - xmean/real(nmean))
     *          + (1-csta)*ysta(i-1)
c
c   trig is array that logs trigger status at each time point
c        trig(i) = 0.0 ===> No trigger declared
c        trig(i) = 1.0 ===> A trigger has been declared
c
         trig(i)=0.0
c
c   fix LTA to STA value after 2 STA time constants
c   just to get the process started
c
         if(i.eq.2*nsta) ylta(i)=ysta(i)
c
c   rat(i) is STA/LTA at each time point
c          rat is not calculated until LTA is initialized
c
         if(i.ge.2*nsta) rat(i)=ysta(i)/ylta(i)
c
c   start triggering after trgdly seconds
c   trgdly should be more than 2 STA time constants
c   
         if(i.ge.ntdly) then
              if(rat(i).ge.ratio) trig(i)=1.0
         endif
c
    3 continue
c
c      find blank in filename
c
      do 4 i=1,32
         if(file(i:i).eq.' ') then
            iblnk=i-1
            go to 5
          endif
    4 continue
      write(6,*) 'no blanks in filename???'
    5 continue
c
c     file.sta contains the STA vs. time trace
c
      file(1:iblnk+4)=file(1:iblnk)//'.sta'
      call wsac1(file,ysta,npts,beg,dt,nerr)
c
c     file.lta contains the LTA vs. time trace
c
      file(1:iblnk+4)=file(1:iblnk)//'.lta'
      call wsac1(file,ylta,npts,beg,dt,nerr)
c
c     file.trig contains the trigger flag vs. time trace
c
      file(1:iblnk+5)=file(1:iblnk)//'.trig'
      call wsac1(file,trig,npts,beg,dt,nerr)
c
c     file.ratio contains the STA/LTA ratio vs. time trace
c
      file(1:iblnk+6)=file(1:iblnk)//'.ratio'
      call wsac1(file,rat,npts,beg,dt,nerr)

      stop 
      end
