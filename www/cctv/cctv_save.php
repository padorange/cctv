<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>&Eacute;dition</title>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
  	<link rel="icon" type="image/png" href="cctv.ico" />
</head>

<body>
  <h1>
Sauvegarde	</h1>
  <p>
  	<?php
			#include config file (define serveur and paths)
			require("config.php");
			
			$connect = mysql_connect($server,$login,$pwd) or die("connect error : ".mysql_error());
			mysql_select_db($database,$connect) or die("select db : ".mysql_error()) ;
			
			$insee=$_POST['id'];
			$nbcam=$_POST['nbcam'];
			$camcomm=$_POST['camcomm'];
			$src1title=$_POST['srctitle'];
			$src1url=$_POST['srcurl'];
			$src2title=$_POST['srctitle2'];
			$src2url=$_POST['srcurl2'];
			$email=$_POST['email'];
	
			echo "<ul><li>INSEE : ".$insee."</li>";
			echo "<li>Cam : ".$nbcam."</li>";
			echo "<li>Comm : ".$camcomm."</li>";
			echo "<li>Src1 : ".$src1title."</li>";
			echo "<li>URL1 : ".$src1url."</li>";
			echo "<li>Src2 : ".$src2title."</li>";
			echo "<li>URL2 : ".$src2url."</li>";
			echo "<li>email : ".$email."</li>";
			
			$query="select * from city where insee='".$insee."'";
			$result = mysql_query($query,$connect) or die("select error : ".mysql_error());		
			$nb=mysql_num_rows($result);
			if ($nb==0)
			{
				$lat='0.0';
				$lon='0.0';
				$name="";
				$county="";
				echo "<li>Commune : NOT FOUND</li>";
			}
			else
			{
				$row = mysql_fetch_array($result);	
				$lat=$row["latitude"];
				$lon=$row["longitude"];
				$name=$row["name"];
				$county=$row["county"];
				echo "<li>Commune : ".$name."</li>";
				echo "<li>Département : ".$county."</li></ul>";
			}
			$query='UPDATE cctv_modif SET nb_actual="'.$nbcam.'", cam_comm="'.$camcomm.'", source_title1="'.$src1title.'", source1="'.$src1url.'", source_title2="'.$src2title.'", source2="'.$src2url.'" WHERE insee="'.$insee.'"';
			$result = mysql_query($query,$connect) or die("select error : ".mysql_error());		
			
			mysql_close($connect);
			
			echo '<a href="'.$root_url.$map_url.'?zoom=12&lat='.$lat.'&lon='.$lon.'">Retour à la carte</a>';

	?>
	 :: <a href="cctv_admin.php">Retour &agrave; la liste</a>	</p>
<!-- Start of StatCounter Code -->
	<script type="text/javascript" language="javascript">
	var sc_project=1651860; 
	var sc_invisible=1; 
	var sc_partition=15; 
	var sc_security="9710e8ad"; 
	</script>
	<script type="text/javascript" language="javascript" src="http://www.statcounter.com/counter/counter.js"></script>
	<noscript>
		<a href="http://www.statcounter.com/" target="_blank">
		<img  src="http://c16.statcounter.com/counter.php?sc_project=1651860&amp;java=0&amp;security=9710e8ad&amp;invisible=1" alt="hit counter script" border="0">
		</a>
	</noscript>
	<!-- End of StatCounter Code -->
</body>
</html>
