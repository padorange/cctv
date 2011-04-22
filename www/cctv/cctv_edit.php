<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<title>&Eacute;dition</title>
	<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
  	<link rel="icon" type="image/png" href="cctv.ico" />
<link href="minimap.css" rel="stylesheet" type="text/css" media="screen" />
    <script type="text/javascript" src="../OpenLayers/OpenLayers.js"></script>
    <script type="text/javascript" src="../osm/OpenStreetMap.js"></script>
    <script type="text/javascript" src="minimap.js"></script>
</head>
<body onload="init()">
  <h1>
&Eacute;dition	</h1>
  <p>
  	<?php
			#include config file (define serveur and paths)
			require("config.php");

			$connect = mysql_connect($server,$login,$pwd) or die("connect error : ".mysql_error());
			mysql_select_db($database,$connect) or die("select db : ".mysql_error()) ;

			if (isset($_GET['insee']))
			{
				$insee=$_GET['insee'];
				$name="";
				$county="";
				$pop='0';
				$lat=='0.0';
				$lon='0.0';
				$nbcam0='0';
				$camcomm0='';
				$src1title0='';
				$src1url0='';
				$src2title0='';
				$src2url0='';
				$nbcam1='0';
				$camcomm1='';
				$src1title1='';
				$src1url1='';
				$src2title1='';
				$src2url1='';
				$email='';
					
				if ($insee<>'0')
				{
					$query="select * from city,cctv where city.insee=cctv.insee and cctv.insee='$insee'";
					$result = mysql_query($query,$connect) or die("select error : ".mysql_error());		
					$nb=mysql_num_rows($result);
					if ($nb==0)
					{
						$insee=-1;
					}
					else
					{
						$row = mysql_fetch_array($result);	
						$lat=$row["latitude"];
						$lon=$row["longitude"];
						$name=$row["name"];
						$county=$row["county"];
						$pop=$row["population"];
						$nbcam0=$row["nb_actual"];
						$camcomm0=$row["cam_comm"];
						$src1title0=$row["source_title1"];
						$src1url0=$row["source1"];
						$src2title0=$row["source_title2"];
						$src2url0=$row["source2"];					
					}
					if ($insee>0)
					{
						$query="select * from cctv_modif where insee='".$insee."';";
						$result = mysql_query($query,$connect) or die("select error : ".mysql_error());		
						$nb=mysql_num_rows($result);
						if ($nb==0)
						{
							$query="insert into cctv_modif (insee,nb_actual,cam_comm,source1,source2,source_title1,source_title2) values ('$insee',$nbcam0,'$camcomm0','$src1url0','$src2url0','$src1title0','$src2title0');";
							$result = mysql_query($query,$connect) or die("select error : ".mysql_error());		
							$nbcam1=$nbcam0;
							$camcomm1=$camcomm0;
							$src1title1=$src1title0;
							$src1url1=$src1url0;
							$src2title1=$src2title0;
							$src2url1=$src2url0;					
						}
						else
						{
							$row = mysql_fetch_array($result);	
							$nbcam1=$row["nb_actual"];
							$camcomm1=$row["cam_comm"];
							$src1title1=$row["source_title1"];
							$src1url1=$row["source1"];
							$src2title1=$row["source_title2"];
							$src2url1=$row["source2"];					
						}	
					}
				}
				else
				{
				
				}
			}
			else
				echo "<p>NO INSEE</p>";
			
			mysql_close($connect);
	?>
	<script type="text/javascript">
	setPosition(<? echo $lat.",".$lon.",12"; ?>);
	</script>
	</p>
  <form id="form1" name="form1" method="post" action=<? echo '"'.$save_url.'?insee='.$insee.'"'; ?>>
  	<table width="100%" border="0" cellpadding="2" cellspacing="0">
		<tr>
			<td valign="top">Code Insee :</td>
			<td valign="top"><?php echo $insee; ?> <input type="hidden" name="id" id="id" value="<?php echo $insee; ?>"></td>
		<td width="300px" rowspan="5"><div id="map"></div></td>
		</tr>
		<tr valign="top">
			<td>Ville </td>
			<td><?php echo $name; ?></td>
		</tr>
		<tr valign="top">
			<td>D&eacute;partement</td>
			<td><?php echo $county; ?></td>
		</tr>
		<tr valign="top">
			<td><label for="nbcam">Nb cam&eacute;ras install&eacute;es</label></td>
			<td><input name="nbcam" type="text" id="nbcam" size="5" <?php echo "value='".$nbcam1."'"; ?> />
			<em>			(indiquer 0, lorsque le nombre est inconnu)</em></td>
		</tr>
		<tr valign="top">
			<td><label for="camcomm">Commentaires</label></td>
			<td><p>
				<textarea name="camcomm" cols="50" rows="8" id="camcomm"><?php echo $camcomm1; ?></textarea>
			</p>
				<p><em>Bien pr&eacute;ciser tout les commentaires n&eacute;cessaires aux informations recceuillies </em></p></td>
		</tr>
	</table>
  	<table width="100%" border="0" cellspacing="0" cellpadding="2">
		<tr>
			<td colspan="3"><h2>Source(s)</h2>
			<p>Vous avez la possibilit&eacute; d'indiquer 2 sources pour les donn&eacute;es recceuillies. Chaque source comprend un 'titre' (ce qui apparaitra &agrave; l'&eacute;cran) et une 'url' (adresse internet, permettant un lien directe vers la page internet correspondant &agrave; la source).<br />
			Si, par exemple, votre source est un article de journal sur internet, pr&eacute;ciser dans 'url' l'adresse internet de la page de l'article et dans 'titre' le nom du journal et la date de l'article.</p>
			</td>
		</tr>
		<tr>
			<td><label for="srctitle">Titre de la source 1</label></td>
			<td><textarea name="srctitle" rows="2" cols="80" id="srctitle"><?php echo $src1title1; ?></textarea></td>
			<td>&nbsp;</td>
		</tr>
		<tr>
			<td><label for="srcurl">Url Source 1</label></td>
			<td><textarea name="srcurl" rows="2" cols="80" id="srcurl"><?php echo $src1url1; ?></textarea></td>
			<td>Tester</td>
		</tr>
		<tr>
			<td><label for="srctitle2">Titre de la source 2</label></td>
			<td><textarea name="srctitle2" rows="2" cols="80" id="srctitle2"><?php echo $src2title1; ?></textarea></td>
			<td>&nbsp;</td>
		</tr>
		<tr>
			<td><label for="srcurl2">Url Source 2</label></td>
			<td><textarea name="srcurl2" rows="2" cols="80" id="srcurl2"><?php echo $src2url1; ?></textarea></td>
			<td>Tester</td>
		</tr>
	</table>
  	<h2>Identification</h2>
  	<p><strong>L'identification est optionnelle.</strong> En indiquant votre email vous nous permettez d'&eacute;ventuellement vous contacter pour recceuillir des pr&eacute;cisions lorsque nous validerons vos donn&eacute;es. Votre email est bien s&ucirc;r totalement confidentiel et ne sera utilis&eacute; pour aucun autre usage, ni utilis&eacute; pour quelque liste que ce soit.</p>
  	<table width="100%" border="0" cellspacing="0" cellpadding="2">
		<tr>
			<td><label for="email">email</label></td>
			<td><input name="email" type="text" id="email" size="40" <?php echo "value='".$email."'"; ?> /></td>
		</tr>
	</table>
	<br />
  	<div align="right">
  		<input type="submit" name="ok" id="ok" value="Valider" />
  		<input type="button" name="button" id="button" value="Annuler" />
  		<br />
	</div>
  	</label>
</form>
  <p>&nbsp;</p>
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
